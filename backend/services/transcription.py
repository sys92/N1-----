import os
import tempfile
import math
import logging
import asyncio
from pydub import AudioSegment
from openai import OpenAI
from models.schemas import TranscriptionResult, TranscriptionSegment

logger = logging.getLogger(__name__)

# 循環インポートを避けるため、必要時にインポート
def get_progress_manager():
    from services.progress_manager import progress_manager
    return progress_manager

class TranscriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def transcribe(self, audio_file_path: str, session_id: str = "default") -> TranscriptionResult:
        """
        OpenAI Whisper APIを使用して音声ファイルを文字起こしする
        大きなファイルは分割して処理する
        """
        try:
            # ファイルサイズをチェック
            file_size = os.path.getsize(audio_file_path)
            max_size = 25 * 1024 * 1024  # 25MB

            if file_size <= max_size:
                # 小さなファイルは直接処理
                return await self._transcribe_single_file(audio_file_path, session_id)
            else:
                # 大きなファイルは分割して処理
                return await self._transcribe_large_file(audio_file_path, session_id)
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    async def _transcribe_single_file(self, audio_file_path: str, session_id: str) -> TranscriptionResult:
        """
        単一ファイルの文字起こし（疑似進捗付き）
        """
        progress_manager = get_progress_manager()

        # 音声ファイルの長さを取得して推定時間を計算
        audio = AudioSegment.from_file(audio_file_path)
        duration_seconds = len(audio) / 1000.0

        # 音声の長さに基づいて推定処理時間を計算（RTF=0.07を使用）
        estimated_time = duration_seconds * 0.07

        await progress_manager.update_progress(session_id, "transcribing", 15, f"音声認識を開始（推定時間: {estimated_time:.1f}秒）...")

        # 疑似進捗を開始
        progress_task = asyncio.create_task(
            self._simulate_transcription_progress(session_id, estimated_time, progress_manager)
        )

        try:
            # 実際の音声認識を実行
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
        finally:
            # 疑似進捗を停止
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

        await progress_manager.update_progress(session_id, "transcription_complete", 75, "音声認識完了")

        return self._process_transcript(transcript)

    async def _simulate_transcription_progress(self, session_id: str, estimated_time: float, progress_manager):
        """
        音声認識中の疑似進捗を表示
        """
        try:
            # 進捗段階を定義（15%から75%まで）
            progress_stages = [
                (20, "音声データを解析中..."),
                (25, "音声パターンを認識中..."),
                (35, "単語を識別中..."),
                (45, "文章を構築中..."),
                (55, "文脈を解析中..."),
                (65, "最終調整中..."),
                (70, "音声認識を完了中...")
            ]

            # 各段階の間隔を計算
            total_stages = len(progress_stages)
            interval = estimated_time / total_stages if estimated_time > 0 else 2.0

            # 最小・最大間隔を設定
            interval = max(1.0, min(interval, 5.0))

            for progress, message in progress_stages:
                await asyncio.sleep(interval)
                await progress_manager.update_progress(session_id, "transcribing", progress, message)

        except asyncio.CancelledError:
            # タスクがキャンセルされた場合（正常終了）
            pass
        except Exception as e:
            logger.error(f"Progress simulation error: {e}")

    async def _simulate_segment_progress(self, session_id: str, start_progress: int, end_progress: int, estimated_time: float, progress_manager, segment_num: int, total_segments: int):
        """
        セグメントごとの疑似進捗を表示
        """
        try:
            # 進捗の範囲を計算
            progress_range = end_progress - start_progress
            steps = 3  # 各セグメントを3段階で進捗表示

            interval = estimated_time / steps if estimated_time > 0 else 1.0
            interval = max(0.5, min(interval, 3.0))

            for step in range(1, steps + 1):
                await asyncio.sleep(interval)
                current_progress = start_progress + int((step / steps) * progress_range)
                await progress_manager.update_progress(
                    session_id,
                    "transcribing",
                    current_progress,
                    f"セグメント {segment_num}/{total_segments} 処理中... (段階{step}/{steps})"
                )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Segment progress simulation error: {e}")

    async def _transcribe_large_file(self, audio_file_path: str, session_id: str) -> TranscriptionResult:
        """
        大きなファイルを分割して文字起こし
        """
        logger.info(f"Large file detected, starting segmentation: {audio_file_path}")
        progress_manager = get_progress_manager()

        # 音声ファイル読み込み開始
        await progress_manager.update_progress(session_id, "loading", 12, "音声ファイルを読み込み中...")

        # 音声ファイルを読み込み
        logger.info(f"Loading audio file: {audio_file_path}")
        audio = AudioSegment.from_file(audio_file_path)

        # 音声ファイルの詳細情報をログ出力
        actual_duration_ms = len(audio)
        actual_duration_seconds = actual_duration_ms / 1000.0
        actual_duration_minutes = actual_duration_seconds / 60.0

        logger.info(f"Audio file loaded successfully:")
        logger.info(f"  Duration: {actual_duration_ms}ms ({actual_duration_seconds:.1f}s, {actual_duration_minutes:.1f}min)")
        logger.info(f"  Sample rate: {audio.frame_rate}Hz")
        logger.info(f"  Channels: {audio.channels}")
        logger.info(f"  Sample width: {audio.sample_width} bytes")

        # コンソールにも出力
        print(f"🎵 AUDIO DEBUG INFO:")
        print(f"  Duration: {actual_duration_ms}ms ({actual_duration_seconds:.1f}s, {actual_duration_minutes:.1f}min)")
        print(f"  Sample rate: {audio.frame_rate}Hz")
        print(f"  Channels: {audio.channels}")
        print(f"  Sample width: {audio.sample_width} bytes")

        await progress_manager.update_progress(session_id, "preparing", 15, f"音声分割の準備中... (音声時間: {actual_duration_minutes:.1f}分)")

        print(f"🔧 [SEGMENTATION] 分割準備開始")

        # 分割設定（25MB制限を確実に下回るように調整）
        segment_duration = 2 * 60 * 1000  # 2分（ミリ秒）
        overlap_duration = 15 * 1000      # 15秒の重複（ミリ秒）

        # 分割数を計算
        total_duration = len(audio)
        num_segments = math.ceil(total_duration / segment_duration)

        print(f"📊 [SEGMENTATION] 分割計画:")
        print(f"  総時間: {total_duration}ms ({total_duration/1000/60:.1f}分)")
        print(f"  セグメント長: {segment_duration}ms ({segment_duration/1000:.0f}秒)")
        print(f"  重複時間: {overlap_duration}ms ({overlap_duration/1000:.0f}秒)")
        print(f"  セグメント数: {num_segments}")

        logger.info(f"Audio duration: {total_duration/1000:.1f}s ({total_duration/1000/60:.1f} minutes)")
        logger.info(f"Segment duration: {segment_duration/1000:.1f}s, Overlap: {overlap_duration/1000:.1f}s")
        logger.info(f"Will create {num_segments} segments")

        await progress_manager.update_progress(
            session_id,
            "segmenting",
            18,
            f"音声を{num_segments}個のセグメントに分割します（総時間: {total_duration/1000/60:.1f}分）"
        )

        # 各セグメントを処理（順番を明確に管理）
        transcripts = []
        temp_files = []

        print(f"🚀 [SEGMENTATION] セグメント処理開始 ({num_segments}個)")

        try:
            for i in range(num_segments):
                segment_index = i  # 明確なインデックス管理

                print(f"🔄 [SEGMENTATION] セグメント {segment_index+1}/{num_segments} 開始")

                try:  # 各セグメントの処理を個別にtry-catch
                    print(f"🔄 Processing segment {segment_index+1}/{num_segments}")

                    # 分割処理の進捗（10%から15%の範囲）
                    segment_progress = 10 + int((segment_index / num_segments) * 5)
                    await progress_manager.update_progress(
                        session_id,
                        "splitting",
                        segment_progress,
                        f"セグメント {segment_index+1}/{num_segments} を切り出し中... (残り{num_segments-segment_index-1}個)"
                    )

                    logger.info(f"Processing segment {segment_index+1}/{num_segments} (index: {segment_index})")

                    start_time = segment_index * segment_duration
                    end_time = min(start_time + segment_duration + overlap_duration, total_duration)

                    print(f"✂️ [SEGMENTATION] セグメント {segment_index+1} 時間: {start_time/1000:.1f}s - {end_time/1000:.1f}s")
                    logger.info(f"Segment {segment_index+1}: {start_time/1000:.1f}s - {end_time/1000:.1f}s")

                    # セグメントを切り出し
                    print(f"🎵 [SEGMENTATION] 音声切り出し中...")
                    segment = audio[start_time:end_time]
                    print(f"✅ [SEGMENTATION] 音声切り出し完了")

                    # セグメントの長さをチェック
                    segment_duration_seconds = len(segment) / 1000.0
                    logger.info(f"Segment {segment_index+1} duration: {segment_duration_seconds:.1f}s")

                    if segment_duration_seconds < 0.1:
                        logger.warning(f"Segment {segment_index+1} is too short ({segment_duration_seconds:.3f}s), skipping...")
                        continue

                    # 一時ファイルに番号付きで保存
                    print(f"💾 [SEGMENTATION] ファイル保存中...")
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_segment_{segment_index:03d}.wav")
                    segment.export(temp_file.name, format="wav")
                    temp_files.append(temp_file.name)
                    print(f"✅ [SEGMENTATION] ファイル保存完了: {temp_file.name}")

                    logger.info(f"Saved segment {segment_index+1} to: {temp_file.name}")

                    # ファイルサイズを確認（25MB制限）
                    file_size = os.path.getsize(temp_file.name)
                    max_segment_size = 25 * 1024 * 1024  # 25MB
                    logger.info(f"Segment {segment_index+1} size: {file_size/1024/1024:.1f}MB")

                    if file_size > max_segment_size:
                        raise Exception(f"Segment {segment_index} size ({file_size} bytes) exceeds 25MB limit")

                    # 文字起こし進捗（15%から78%の範囲）
                    base_progress = 15 + int((segment_index / num_segments) * 63)
                    await progress_manager.update_progress(
                        session_id,
                        "transcribing",
                        base_progress,
                        f"セグメント {segment_index+1}/{num_segments} を文字起こし中... ({file_size/1024/1024:.1f}MB)"
                    )

                    # WebSocket送信を確実にするための短い待機
                    await asyncio.sleep(0.1)

                    # 文字起こし実行（タイムアウト・リトライ付き）
                    logger.info(f"Transcribing segment {segment_index+1}...")
                    print(f"🎤 [TRANSCRIPTION] セグメント {segment_index+1} OpenAI API呼び出し開始")

                    transcript = None
                    max_retries = 3

                    for retry in range(max_retries):
                        try:
                            print(f"🔄 [TRANSCRIPTION] API呼び出し試行 {retry+1}/{max_retries}")

                            with open(temp_file.name, "rb") as audio_file:
                                # タイムアウト付きでAPI呼び出し
                                transcript = await asyncio.wait_for(
                                    asyncio.to_thread(
                                        lambda: self.client.audio.transcriptions.create(
                                            model="whisper-1",
                                            file=audio_file,
                                            response_format="verbose_json"
                                        )
                                    ),
                                    timeout=120.0  # 2分タイムアウト
                                )
                            print(f"✅ [TRANSCRIPTION] API呼び出し成功")
                            break

                        except asyncio.TimeoutError:
                            print(f"⏰ [TRANSCRIPTION] API呼び出しタイムアウト (試行 {retry+1}/{max_retries})")
                            if retry == max_retries - 1:
                                raise Exception(f"OpenAI API timeout after {max_retries} retries")
                            await asyncio.sleep(5)  # 5秒待機してリトライ

                        except Exception as e:
                            print(f"❌ [TRANSCRIPTION] API呼び出しエラー: {e} (試行 {retry+1}/{max_retries})")
                            if retry == max_retries - 1:
                                raise
                            await asyncio.sleep(5)  # 5秒待機してリトライ

                    # 文字起こし結果をログ出力
                    transcript_text = getattr(transcript, 'text', 'No text available')
                    transcript_duration = getattr(transcript, 'duration', (end_time - start_time) / 1000.0)

                    logger.info(f"Segment {segment_index+1} transcription completed:")
                    logger.info(f"  Index: {segment_index}")
                    logger.info(f"  Duration: {transcript_duration:.1f}s")
                    logger.info(f"  Text length: {len(transcript_text)} characters")
                    logger.info(f"  Text preview: {transcript_text[:100]}...")

                    print(f"✅ Segment {segment_index+1} completed: {len(transcript_text)} chars")

                    # セグメント完了時の進捗更新
                    completed_progress = 15 + int(((segment_index + 1) / num_segments) * 63)
                    await progress_manager.update_progress(
                        session_id,
                        "transcribing",
                        completed_progress,
                        f"セグメント {segment_index+1}/{num_segments} 完了 ({len(transcript_text)}文字)"
                    )

                    # WebSocket送信を確実にするための短い待機
                    await asyncio.sleep(0.1)

                    transcripts.append({
                        'index': segment_index,  # 順番情報を追加
                        'transcript': transcript,
                        'start_offset': start_time / 1000.0,  # 秒に変換
                        'duration': transcript_duration,
                        'original_start_time': start_time / 1000.0,
                        'original_end_time': end_time / 1000.0
                    })

                except Exception as segment_error:
                    logger.error(f"Error processing segment {segment_index+1}: {segment_error}")
                    print(f"❌ Error in segment {segment_index+1}: {segment_error}")
                    # セグメントエラーでも処理を続行
                    continue

            # マージ処理の進捗
            await progress_manager.update_progress(session_id, "merging", 78, "文字起こし結果をマージ中...")

            # 文字起こし結果をマージ
            logger.info("Merging transcription results...")
            result = self._merge_transcripts(transcripts, overlap_duration / 1000.0)

            await progress_manager.update_progress(session_id, "transcription_complete", 78, "音声認識完了")
            logger.info("Large file transcription completed successfully")
            return result

        finally:
            # 一時ファイルを削除
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def _merge_transcripts(self, transcripts, overlap_duration: float) -> TranscriptionResult:
        """
        分割された文字起こし結果をマージ
        """
        logger.info(f"Merging {len(transcripts)} transcript segments")
        logger.info(f"Overlap duration: {overlap_duration:.1f}s")

        if not transcripts:
            return TranscriptionResult(segments=[], full_text="")

        # 順番を確実にソート
        transcripts.sort(key=lambda x: x['index'])
        logger.info("Sorted transcripts by index:")
        for i, t in enumerate(transcripts):
            logger.info(f"  Position {i}: Index {t['index']}, Start: {t['original_start_time']:.1f}s")

        # 改善された重複処理を有効化
        use_overlap_processing = True  # 重複処理を有効化
        logger.info(f"Overlap processing: {'enabled' if use_overlap_processing else 'disabled (debug mode)'}")

        # 最初のトランスクリプトを基準とする
        merged_segments = []
        cumulative_duration = 0

        for i, transcript_data in enumerate(transcripts):
            transcript = transcript_data['transcript']
            start_offset = cumulative_duration

            logger.info(f"Processing transcript {i+1}/{len(transcripts)}")
            logger.info(f"  Start offset: {start_offset:.1f}s")
            logger.info(f"  Duration: {transcript_data['duration']:.1f}s")

            segments_added = 0
            segments_skipped = 0

            if hasattr(transcript, 'segments') and transcript.segments:
                logger.info(f"  Found {len(transcript.segments)} segments in transcript {i+1}")

                for j, segment in enumerate(transcript.segments):
                    # segmentの処理
                    if isinstance(segment, dict):
                        start = segment.get('start', 0)
                        end = segment.get('end', 0)
                        text = segment.get('text', '').strip()
                    else:
                        start = getattr(segment, 'start', 0)
                        end = getattr(segment, 'end', 0)
                        text = getattr(segment, 'text', '').strip()

                    # 時刻を補正
                    adjusted_start = start + start_offset
                    adjusted_end = end + start_offset

                    # 重複部分の処理（最初のセグメント以外）
                    skip_segment = False
                    if use_overlap_processing and i > 0:
                        # 改善された重複処理: セグメント内の相対時間で判定
                        # 各セグメントは2分(120秒) + 15秒重複 = 135秒
                        # 重複部分は最初の15秒なので、15秒以降のセグメントのみ保持
                        if start < overlap_duration:
                            skip_segment = True
                            segments_skipped += 1
                            logger.debug(f"    Skipping segment {j+1} (overlap): {start:.1f}s < {overlap_duration:.1f}s")
                        else:
                            logger.debug(f"    Keeping segment {j+1} (beyond overlap): {start:.1f}s >= {overlap_duration:.1f}s")
                    else:
                        logger.debug(f"    Keeping segment {j+1} (first segment or overlap disabled): {start:.1f}s")

                    if not skip_segment:
                        merged_segments.append(TranscriptionSegment(
                            start=adjusted_start,
                            end=adjusted_end,
                            text=text
                        ))
                        segments_added += 1
                        logger.debug(f"    Added segment {j+1}: {adjusted_start:.1f}s-{adjusted_end:.1f}s")

            logger.info(f"  Segments added: {segments_added}, skipped: {segments_skipped}")

            # 累積時間を更新（重複期間を除く）
            if use_overlap_processing:
                if i < len(transcripts) - 1:  # 最後以外
                    cumulative_duration += transcript_data['duration'] - overlap_duration
                    logger.info(f"  Updated cumulative duration: {cumulative_duration:.1f}s (removed {overlap_duration:.1f}s overlap)")
                else:  # 最後
                    cumulative_duration += transcript_data['duration']
                    logger.info(f"  Final cumulative duration: {cumulative_duration:.1f}s")
            else:
                # デバッグモード: 重複を考慮せずに単純に加算
                if i == 0:
                    cumulative_duration = transcript_data['duration']
                else:
                    # 2分間隔で分割しているので、2分ずつ加算
                    cumulative_duration += 2 * 60  # 2分 = 120秒
                logger.info(f"  Debug mode cumulative duration: {cumulative_duration:.1f}s")

        result = self._build_result(merged_segments)

        logger.info(f"Merge completed:")
        logger.info(f"  Total segments: {len(merged_segments)}")
        logger.info(f"  Total text length: {len(result.full_text)} characters")
        logger.info(f"  Final duration: {cumulative_duration:.1f}s ({cumulative_duration/60:.1f} minutes)")

        return result

    def _process_transcript(self, transcript) -> TranscriptionResult:
        """
        単一のトランスクリプトを処理
        """
        segments = []

        if hasattr(transcript, 'segments') and transcript.segments:
            for segment in transcript.segments:
                if isinstance(segment, dict):
                    start = segment.get('start', 0)
                    end = segment.get('end', 0)
                    text = segment.get('text', '').strip()
                else:
                    start = getattr(segment, 'start', 0)
                    end = getattr(segment, 'end', 0)
                    text = getattr(segment, 'text', '').strip()

                segments.append(TranscriptionSegment(
                    start=start,
                    end=end,
                    text=text
                ))

        return self._build_result(segments)

    def _build_result(self, segments) -> TranscriptionResult:
        """
        セグメントからTranscriptionResultを構築
        """
        full_text_parts = []

        for segment in segments:
            start_time = self._format_timestamp(segment.start)
            full_text_parts.append(f"【{start_time}】{segment.text}")

        if not full_text_parts:
            full_text_parts.append("【00:00:00】音声の文字起こしができませんでした")

        full_text = "\n".join(full_text_parts)

        return TranscriptionResult(
            segments=segments,
            full_text=full_text
        )

    def _format_timestamp(self, seconds: float) -> str:
        """
        秒数をHH:MM:SS形式に変換
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
