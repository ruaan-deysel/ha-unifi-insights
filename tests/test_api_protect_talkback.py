# Copyright 2026 UniFi Insights contributors
"""Tests for UniFi Protect talkback audio transport."""

from __future__ import annotations

import sys
import threading
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.unifi_insights.api.protect.models.files import TalkbackSession
from custom_components.unifi_insights.api.protect.talkback import (
    TalkbackCodecError,
    TalkbackError,
    TalkbackImportError,
    TalkbackSamplingRateError,
    TalkbackSchemeError,
    TalkbackStream,
    TalkbackStreamError,
    _sanitize_url,
    _transcode_and_stream,
    validate_talkback_session,
)


def _make_session(
    url: str = "rtp://192.168.1.10:7004",
    codec: str = "opus",
    sampling_rate: int = 24000,
    bits_per_sample: int = 16,
) -> TalkbackSession:
    """Helper to construct a TalkbackSession."""
    return TalkbackSession(
        url=url,
        codec=codec,
        samplingRate=sampling_rate,
        bitsPerSample=bits_per_sample,
    )


def test_validate_talkback_session_valid() -> None:
    """Test valid talkback session configurations."""
    # RTP + Opus
    validate_talkback_session(_make_session("rtp://10.0.0.1:7004", "opus", 24000, 16))
    # UDP + AAC
    validate_talkback_session(_make_session("udp://10.0.0.1:7004", "aac", 44100, 16))
    # Vorbis
    validate_talkback_session(_make_session("rtp://10.0.0.1:7004", "vorbis", 48000, 16))


def test_validate_talkback_session_invalid_url() -> None:
    """Test invalid or unsupported talkback session URLs."""
    # Missing URL
    with pytest.raises(TalkbackSchemeError, match="Talkback session URL is required"):
        validate_talkback_session(_make_session(url=""))

    # Unsupported scheme (wss://)
    with pytest.raises(
        TalkbackSchemeError, match="Unsupported talkback URL scheme: 'wss'"
    ):
        validate_talkback_session(_make_session(url="wss://10.0.0.1:7004"))

    # Unsupported scheme (http://)
    with pytest.raises(
        TalkbackSchemeError, match="Unsupported talkback URL scheme: 'http'"
    ):
        validate_talkback_session(_make_session(url="http://10.0.0.1:7004"))


def test_validate_talkback_session_invalid_codec() -> None:
    """Test invalid or unsupported talkback session codecs."""
    # Missing codec
    with pytest.raises(TalkbackCodecError, match="Talkback session codec is required"):
        validate_talkback_session(_make_session(codec=""))

    # Unsupported codec
    with pytest.raises(TalkbackCodecError, match="Unsupported talkback codec: 'mp3'"):
        validate_talkback_session(_make_session(codec="mp3"))


@pytest.mark.parametrize("rate", [0, -1, None, "24000", True])
def test_validate_talkback_session_invalid_sampling_rate(rate: int) -> None:
    """Test invalid sampling rates."""
    session = _make_session()
    # Bypass Pydantic validation by setting attribute directly
    object.__setattr__(session, "sampling_rate", rate)
    with pytest.raises(
        TalkbackSamplingRateError, match="Invalid talkback sampling rate"
    ):
        validate_talkback_session(session)


def test_transcode_and_stream_missing_pyav() -> None:
    """Test TalkbackImportError when PyAV is not installed."""
    session = _make_session()
    stop_event = threading.Event()

    with (
        patch.dict(sys.modules, {"av": None, "av.audio.resampler": None}),
        pytest.raises(TalkbackImportError, match="PyAV is required"),
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)


def test_transcode_and_stream_open_input_failure() -> None:
    """Test TalkbackStreamError when opening source media fails."""
    session = _make_session()
    stop_event = threading.Event()

    mock_av = MagicMock()
    mock_av.open.side_effect = RuntimeError("File not found")

    with (
        patch.dict(
            sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
        ),
        pytest.raises(TalkbackStreamError, match="Failed to open source media"),
    ):
        _transcode_and_stream(session, "missing.mp3", stop_event)


def test_transcode_and_stream_no_audio_streams() -> None:
    """Test TalkbackStreamError when source media has no audio streams."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = []

    mock_av = MagicMock()
    mock_av.open.return_value = mock_input

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        with pytest.raises(TalkbackStreamError, match="No audio streams found"):
            _transcode_and_stream(session, "silent.mp4", stop_event)
        mock_input.close.assert_called_once()


def test_transcode_and_stream_open_output_failure() -> None:
    """Test TalkbackStreamError when opening destination stream fails."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]

    mock_av = MagicMock()
    # First call succeeds (input), second call raises (output)
    mock_av.open.side_effect = [mock_input, RuntimeError("Cannot bind socket")]

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        with pytest.raises(
            TalkbackStreamError, match="Failed to open destination stream"
        ):
            _transcode_and_stream(session, "media.mp3", stop_event)
        mock_input.close.assert_called_once()


def test_transcode_and_stream_open_input_failure_redacts_query() -> None:
    """Test TalkbackStreamError redacts query parameters from source URL."""
    session = _make_session()
    stop_event = threading.Event()

    mock_av = MagicMock()
    mock_av.open.side_effect = RuntimeError("File not found")

    with (
        patch.dict(
            sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
        ),
        pytest.raises(TalkbackStreamError) as exc_info,
    ):
        _transcode_and_stream(
            session,
            "http://user:password@ha.local/media.mp3?authSig=supersecret123#fragment",
            stop_event,
        )

    err_msg = str(exc_info.value)
    assert "user:password@" not in err_msg
    assert "password" not in err_msg
    assert "supersecret123" not in err_msg
    assert "fragment" not in err_msg
    assert "http://ha.local/media.mp3" in err_msg


def test_transcode_and_stream_open_output_failure_redacts_query() -> None:
    """Test TalkbackStreamError redacts credentials from destination URL."""
    session = _make_session(
        url="rtp://user:password@192.168.1.10:7004?token=secrettoken#frag"
    )
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, RuntimeError("Cannot bind socket")]

    with (
        patch.dict(
            sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
        ),
        pytest.raises(TalkbackStreamError) as exc_info,
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)

    err_msg = str(exc_info.value)
    assert "user:password@" not in err_msg
    assert "password" not in err_msg
    assert "secrettoken" not in err_msg
    assert "frag" not in err_msg
    assert "rtp://192.168.1.10:7004" in err_msg


def test_sanitize_url_helper() -> None:
    """Test _sanitize_url strips userinfo, parameters, fragments, and bad URLs."""
    assert (
        _sanitize_url("http://example.com/audio.mp3?key=val#frag")
        == "http://example.com/audio.mp3"
    )
    assert (
        _sanitize_url("http://user:pass@example.com/audio.mp3?key=val#frag")
        == "http://example.com/audio.mp3"
    )
    assert (
        _sanitize_url("rtp://admin:secret@192.168.1.10:7004")
        == "rtp://192.168.1.10:7004"
    )
    assert _sanitize_url("/local/doorbell.wav?authSig=abc") == "/local/doorbell.wav"
    assert _sanitize_url("rtp://192.168.1.10:7004") == "rtp://192.168.1.10:7004"
    with patch("urllib.parse.urlsplit", side_effect=ValueError("bad")):
        assert _sanitize_url("anything") == "<invalid-url>"


@pytest.mark.parametrize(
    ("bit_depth", "expected_fmt"),
    [(8, "u8"), (16, "s16"), (32, "s32"), (24, "s16")],
)
def test_transcode_and_stream_bit_depth_mapping(
    bit_depth: int, expected_fmt: str
) -> None:
    """Test bit-depth mapping and fallback."""
    session = _make_session(bits_per_sample=bit_depth)
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    mock_input.decode.return_value = []

    mock_output = MagicMock()
    mock_stream = MagicMock()
    mock_stream.format = None
    mock_output.add_stream.return_value = mock_stream

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_resampler_cls = MagicMock()
    mock_av.audio.resampler.AudioResampler = mock_resampler_cls

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)

        mock_resampler_cls.assert_called_once_with(
            format=expected_fmt,
            layout="mono",
            rate=session.sampling_rate,
        )


def test_transcode_and_stream_playback_success() -> None:
    """Test full playback loop transcoding, pacing, and flushing."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input_stream = MagicMock()
    mock_input.streams.audio = [mock_input_stream]

    # Two input frames
    frame1 = MagicMock()
    frame2 = MagicMock()
    mock_input.decode.return_value = [frame1, frame2]

    # Resampled frames
    r_frame1 = MagicMock(samples=480)
    r_frame2 = MagicMock(samples=480)
    flush_frame = MagicMock(samples=240)

    mock_resampler = MagicMock()
    mock_resampler.resample.side_effect = [
        [r_frame1],
        [r_frame2],
        [flush_frame],  # flush resample(None)
    ]

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output_stream.format = "s16"
    mock_output.add_stream.return_value = mock_output_stream

    packet1 = MagicMock()
    packet2 = MagicMock()
    packet3 = MagicMock()
    packet_final = MagicMock()

    # encode calls
    mock_output_stream.encode.side_effect = [
        [packet1],
        [packet2],
        [packet3],
        [packet_final],
    ]

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)

        assert mock_output.mux.call_count == 4
        mock_input.close.assert_called_once()
        mock_output.close.assert_called_once()


def test_transcode_and_stream_cooperative_stop_between_frames() -> None:
    """Test cooperative stop between input frames skips encoder flush."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]

    frame1 = MagicMock()
    frame2 = MagicMock()
    mock_input.decode.return_value = [frame1, frame2]

    r_frame1 = MagicMock(samples=480)

    def _resample_side_effect(frame: Any) -> list[Any]:
        if frame is frame1:
            return [r_frame1]
        if frame is frame2:
            stop_event.set()
            return []
        return []

    mock_resampler = MagicMock()
    mock_resampler.resample.side_effect = _resample_side_effect

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output.add_stream.return_value = mock_output_stream
    mock_output_stream.encode.return_value = [MagicMock()]

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)

        # encode should have been called only for r_frame1, and no flush encode(None)
        mock_output_stream.encode.assert_called_once_with(r_frame1)


def test_transcode_and_stream_cooperative_stop_during_pacing() -> None:
    """Test cooperative stop during Event.wait pacing."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    # Two frames so that on the second frame played_duration > 0 and delay > 0
    frame1 = MagicMock()
    frame2 = MagicMock()
    mock_input.decode.return_value = [frame1, frame2]

    r_frame1 = MagicMock(samples=24000)  # 1 second of audio
    r_frame2 = MagicMock(samples=24000)

    mock_resampler = MagicMock()
    mock_resampler.resample.side_effect = [[r_frame1], [r_frame2]]

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output.add_stream.return_value = mock_output_stream
    mock_output_stream.encode.return_value = []

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    # Simulate stop_event being set during pacing wait
    def _fake_wait(timeout: float) -> bool:
        stop_event.set()
        return True

    with patch.object(stop_event, "wait", side_effect=_fake_wait) as mock_wait:
        with patch.dict(
            sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
        ):
            _transcode_and_stream(session, "media.mp3", stop_event)

        assert mock_wait.called
        assert stop_event.is_set()


def test_transcode_and_stream_close_exceptions_suppressed() -> None:
    """Test exceptions during container close are safely ignored."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    mock_input.decode.return_value = []
    mock_input.close.side_effect = RuntimeError("Input close error")

    mock_output = MagicMock()
    mock_output.add_stream.return_value = MagicMock()
    mock_output.close.side_effect = RuntimeError("Output close error")

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)


@pytest.mark.asyncio
async def test_talkback_stream_lifecycle(hass: Any) -> None:
    """Test TalkbackStream start, running, stop, and complete."""
    session = _make_session()
    stream = TalkbackStream(session, "media.mp3", hass)

    assert not stream.running

    with patch(
        "custom_components.unifi_insights.api.protect.talkback._transcode_and_stream"
    ) as mock_worker:
        # Start
        await stream.start()
        # Double start is a no-op
        await stream.start()

        # Wait until finished
        await stream.wait_until_complete()

        mock_worker.assert_called_once_with(session, "media.mp3", stream._stop_event)
        assert not stream.running

        # Idempotent stop
        await stream.stop()
        await stream.stop()


@pytest.mark.asyncio
async def test_talkback_stream_worker_error_propagation(hass: Any) -> None:
    """Test worker error propagation through wait_until_complete."""
    session = _make_session()
    stream = TalkbackStream(session, "media.mp3", hass)

    with patch(
        "custom_components.unifi_insights.api.protect.talkback._transcode_and_stream",
        side_effect=TalkbackStreamError("Worker crash"),
    ):
        await stream.start()

        # Stop should not raise despite worker error
        await stream.stop()

        with pytest.raises(TalkbackStreamError, match="Worker crash"):
            await stream.wait_until_complete()


@pytest.mark.asyncio
async def test_talkback_stream_wait_until_complete_stored_error(hass: Any) -> None:
    """Test wait_until_complete re-raises stored _error if worker task is None."""
    session = _make_session()
    stream = TalkbackStream(session, "media.mp3", hass)
    stream._error = TalkbackError("Pre-existing error")

    with pytest.raises(TalkbackError, match="Pre-existing error"):
        await stream.wait_until_complete()


def test_transcode_and_stream_stop_before_next_decode_frame() -> None:
    """Test stop_event.is_set() at the start of decode frame loop."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    frame1 = MagicMock()
    frame2 = MagicMock()
    mock_input.decode.return_value = [frame1, frame2]

    r_frame1 = MagicMock(samples=480)

    def _resample(frame: Any) -> list[Any]:
        stop_event.set()
        return [r_frame1]

    mock_resampler = MagicMock()
    mock_resampler.resample.side_effect = _resample

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output.add_stream.return_value = mock_output_stream
    mock_output_stream.encode.return_value = []

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)


def test_transcode_and_stream_stop_inside_resampled_frames() -> None:
    """Test stop_event.is_set() inside inner resampled frame loop."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    mock_input.decode.return_value = [MagicMock()]

    r_frame1 = MagicMock(samples=480)
    r_frame2 = MagicMock(samples=480)

    mock_resampler = MagicMock()
    mock_resampler.resample.return_value = [r_frame1, r_frame2]

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output.add_stream.return_value = mock_output_stream

    def _encode(rf: Any) -> list[Any]:
        stop_event.set()
        return []

    mock_output_stream.encode.side_effect = _encode

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    with patch.dict(
        sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)


def test_transcode_and_stream_stop_when_delay_negative() -> None:
    """Test delay <= 0 and stop_event.is_set() branch at line 207."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    mock_input.decode.return_value = [MagicMock()]

    r_frame = MagicMock(samples=480)
    mock_resampler = MagicMock()

    def _resample(frame: Any) -> list[Any]:
        stop_event.set()
        return [r_frame]

    mock_resampler.resample.side_effect = _resample

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output.add_stream.return_value = mock_output_stream
    mock_output_stream.encode.return_value = []

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    # Patch time.monotonic to return a large value so delay <= 0
    with (
        patch("time.monotonic", return_value=99999999.0),
        patch.dict(
            sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
        ),
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)


def test_transcode_and_stream_generic_runtime_error_during_mux() -> None:
    """Test generic Exception during loop wrapped into TalkbackStreamError."""
    session = _make_session()
    stop_event = threading.Event()

    mock_input = MagicMock()
    mock_input.streams.audio = [MagicMock()]
    mock_input.decode.return_value = [MagicMock()]

    mock_resampler = MagicMock()
    mock_resampler.resample.return_value = [MagicMock(samples=480)]

    mock_output = MagicMock()
    mock_output_stream = MagicMock()
    mock_output.add_stream.return_value = mock_output_stream
    mock_output_stream.encode.return_value = [MagicMock()]
    mock_output.mux.side_effect = RuntimeError("Broken pipe")

    mock_av = MagicMock()
    mock_av.open.side_effect = [mock_input, mock_output]
    mock_av.audio.resampler.AudioResampler.return_value = mock_resampler

    with (
        patch.dict(
            sys.modules, {"av": mock_av, "av.audio.resampler": mock_av.audio.resampler}
        ),
        pytest.raises(
            TalkbackStreamError, match="Error during talkback stream: Broken pipe"
        ),
    ):
        _transcode_and_stream(session, "media.mp3", stop_event)


@pytest.mark.asyncio
async def test_talkback_stream_stop_before_start(hass: Any) -> None:
    """Test stop() when stream has not been started."""
    session = _make_session()
    stream = TalkbackStream(session, "media.mp3", hass)
    await stream.stop()
    assert not stream.running


@pytest.mark.asyncio
async def test_talkback_stream_wait_until_complete_unstarted(hass: Any) -> None:
    """Test wait_until_complete() when stream has not been started and no error."""
    session = _make_session()
    stream = TalkbackStream(session, "media.mp3", hass)
    await stream.wait_until_complete()
