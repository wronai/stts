#!/usr/bin/env bash
# Benchmark STT and TTS providers - timing and accuracy matrix
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
SAMPLES="$ROOT/python/samples"
VENV="$ROOT/venv/bin/python"
TMP_DIR="/tmp/stts_benchmark_$$"
METRICS_PY="$ROOT/examples/bench_metrics.py"
OUT_CSV="$TMP_DIR/results.csv"

# Use venv python if available
if [ -f "$VENV" ]; then
  PYTHON="$VENV"
else
  PYTHON="python3"
fi

mkdir -p "$TMP_DIR"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

_ts() {
  # monotonic timestamp in seconds (float)
  "$PYTHON" - <<'PY'
import time
print(f"{time.perf_counter():.9f}")
PY
}

_dt() {
  # delta seconds = end - start
  "$PYTHON" - "$1" "$2" <<'PY'
import sys
start=float(sys.argv[1]); end=float(sys.argv[2])
print(f"{(end-start):.6f}")
PY
}

_fmt() {
  # format float seconds to 2 decimals
  "$PYTHON" - "$1" <<'PY'
import sys
v=float(sys.argv[1])
print(f"{v:.2f}")
PY
}

_wer() {
  "$PYTHON" "$METRICS_PY" wer "$1" "$2" 2>/dev/null || echo "1.0000"
}

_cer() {
  "$PYTHON" "$METRICS_PY" cer "$1" "$2" 2>/dev/null || echo "1.0000"
}

_ratio() {
  "$PYTHON" "$METRICS_PY" ratio "$1" "$2" 2>/dev/null || echo "0.0000"
}

_stats() {
  # prints: avg,p50,p95,min,max
  "$PYTHON" "$METRICS_PY" stats "$@" 2>/dev/null || echo "0,0,0,0,0"
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          STTS Benchmark - STT/TTS Performance Matrix          ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# STT Benchmark
# ============================================================================

STT_PROVIDERS=("whisper_cpp" "vosk")
STT_MODELS=("" "small-pl")  # whisper uses default, vosk uses small-pl

# Sample files with expected transcriptions
declare -A SAMPLES_EXPECTED
SAMPLES_EXPECTED["cmd_echo_hello.wav"]="echo hello"
SAMPLES_EXPECTED["cmd_ls.wav"]="ls"

_expected_for() {
  local wav_path="$1"
  local sidecar="${wav_path}.txt"
  if [ -f "$sidecar" ]; then
    cat "$sidecar"
    return 0
  fi
  local base
  base="$(basename "$wav_path")"
  if [ -n "${SAMPLES_EXPECTED[$base]+x}" ]; then
    printf "%s" "${SAMPLES_EXPECTED[$base]}"
    return 0
  fi
  echo ""
}

echo "provider,kind,sample,expected,transcript,time_s,wer,cer,ratio,tts_provider" > "$OUT_CSV"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  STT Benchmark${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

printf "%-15s %-20s %-10s %-10s %-10s %-10s %-12s\n" "Provider" "Sample" "Time(s)" "WER" "CER" "Sim" "Transcription"
echo "─────────────────────────────────────────────────────────────────────────────────"

STT_RESULTS=()

for i in "${!STT_PROVIDERS[@]}"; do
  provider="${STT_PROVIDERS[$i]}"
  model="${STT_MODELS[$i]}"
  
  for sample in "${!SAMPLES_EXPECTED[@]}"; do
    sample_path="$SAMPLES/$sample"
    expected="$(_expected_for "$sample_path")"
    
    if [ ! -f "$sample_path" ]; then
      continue
    fi
    
    # Build command
    cmd="$PYTHON $STTS --stt-provider $provider"
    if [ -n "$model" ]; then
      cmd="$cmd --stt-model $model"
    fi
    cmd="$cmd --stt-file $sample_path --stt-only"
    
    # Measure time
    start_time=$(_ts)
    result=$(eval "$cmd" 2>/dev/null | tail -1) || result=""
    end_time=$(_ts)
    elapsed_raw=$(_dt "$start_time" "$end_time")
    elapsed=$(_fmt "$elapsed_raw")

    wer=$(_wer "$expected" "$result")
    cer=$(_cer "$expected" "$result")
    sim=$(_ratio "$expected" "$result")

    # Colorize WER (lower is better)
    acc_color="$GREEN"
    if "$PYTHON" - "$wer" <<'PY' >/dev/null 2>&1
import sys
wer=float(sys.argv[1])
sys.exit(0 if wer <= 0.25 else 1)
PY
    then
      acc_color="$GREEN"
    elif "$PYTHON" - "$wer" <<'PY' >/dev/null 2>&1
import sys
wer=float(sys.argv[1])
sys.exit(0 if wer <= 0.60 else 1)
PY
    then
      acc_color="$YELLOW"
    else
      acc_color="$RED"
    fi
    
    # Truncate result for display
    result_display="${result:0:18}"
    if [ ${#result} -gt 18 ]; then
      result_display="${result_display}..."
    fi
    
    printf "%-15s %-20s %-10s ${acc_color}%-10s${NC} %-10s %-10s %-12s\n" \
      "$provider" "${sample%.wav}" "${elapsed}s" "$wer" "$cer" "$sim" "$result_display"

    echo "${provider},stt,${sample},\"${expected}\",\"${result}\",${elapsed_raw},${wer},${cer},${sim}," >> "$OUT_CSV"
    STT_RESULTS+=("$provider|$sample|$elapsed_raw|$wer|$cer|$sim|$result")
  done
done

echo ""

# ============================================================================
# TTS Benchmark
# ============================================================================

TTS_PROVIDERS=("piper" "espeak")
TTS_VOICES=("pl" "pl")

# Test phrases
TTS_PHRASES=(
  "Cześć, to jest test"
  "Szybki brązowy lis przeskoczył przez płot"
  "Jeden dwa trzy cztery pięć"
)

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  TTS Benchmark${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

printf "%-15s %-10s %-40s %-10s\n" "Provider" "Voice" "Phrase" "Time(s)"
echo "─────────────────────────────────────────────────────────────────────────────────"

TTS_RESULTS=()

for i in "${!TTS_PROVIDERS[@]}"; do
  provider="${TTS_PROVIDERS[$i]}"
  voice="${TTS_VOICES[$i]}"
  
  for phrase in "${TTS_PHRASES[@]}"; do
    # Measure time
    start_time=$(_ts)
    STTS_TTS_PROVIDER="$provider" STTS_TTS_VOICE="$voice" \
      $PYTHON $STTS --tts-test "$phrase" >/dev/null 2>&1 || true
    end_time=$(_ts)
    elapsed_raw=$(_dt "$start_time" "$end_time")
    elapsed=$(_fmt "$elapsed_raw")
    
    # Truncate phrase for display
    phrase_display="${phrase:0:38}"
    if [ ${#phrase} -gt 38 ]; then
      phrase_display="${phrase_display}..."
    fi
    
    printf "%-15s %-10s %-40s %-10s\n" \
      "$provider" "$voice" "$phrase_display" "${elapsed}s"

    echo "${provider},tts,phrase,\"${phrase}\",,${elapsed_raw},,,,${provider}" >> "$OUT_CSV"
    TTS_RESULTS+=("$provider|$voice|$phrase|$elapsed_raw")
  done
done

echo ""

# ============================================================================
# Cross Matrix: STT + TTS Pipeline
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  STT→TTS Pipeline Matrix${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Testing: audio → STT → transcription → TTS → speak"
echo ""

printf "%-15s %-15s %-20s %-12s %-10s %-10s\n" "STT" "TTS" "Sample" "Total(s)" "WER" "Text"
echo "─────────────────────────────────────────────────────────────────────────────────"

PIPELINE_RESULTS=()

for si in "${!STT_PROVIDERS[@]}"; do
  stt_provider="${STT_PROVIDERS[$si]}"
  stt_model="${STT_MODELS[$si]}"
  
  for ti in "${!TTS_PROVIDERS[@]}"; do
    tts_provider="${TTS_PROVIDERS[$ti]}"
    tts_voice="${TTS_VOICES[$ti]}"
    
    for sample in "${!SAMPLES_EXPECTED[@]}"; do
      sample_path="$SAMPLES/$sample"
      
      if [ ! -f "$sample_path" ]; then
        continue
      fi
      
      # Build STT command
      stt_cmd="$PYTHON $STTS --stt-provider $stt_provider"
      if [ -n "$stt_model" ]; then
        stt_cmd="$stt_cmd --stt-model $stt_model"
      fi
      stt_cmd="$stt_cmd --stt-file $sample_path --stt-only"
      
      # Full pipeline timing
      start_time=$(_ts)
      
      # Step 1: STT
      transcription=$(eval "$stt_cmd" 2>/dev/null | tail -1) || transcription=""
      
      expected="$(_expected_for "$sample_path")"
      wer=$(_wer "$expected" "$transcription")

      # Step 2: TTS (speak transcription)
      if [ -n "$transcription" ]; then
        STTS_TTS_PROVIDER="$tts_provider" STTS_TTS_VOICE="$tts_voice" \
          $PYTHON $STTS --tts-test "$transcription" >/dev/null 2>&1 || true
      fi

      end_time=$(_ts)
      elapsed_raw=$(_dt "$start_time" "$end_time")
      elapsed=$(_fmt "$elapsed_raw")

      txt_disp="${transcription:0:12}"
      if [ ${#transcription} -gt 12 ]; then
        txt_disp="${txt_disp}..."
      fi

      printf "%-15s %-15s %-20s %-12s %-10s %-10s\n" \
        "$stt_provider" "$tts_provider" "${sample%.wav}" "${elapsed}s" "$wer" "$txt_disp"

      echo "${stt_provider},pipeline,${sample},\"${expected}\",\"${transcription}\",${elapsed_raw},${wer},,,${tts_provider}" >> "$OUT_CSV"
      PIPELINE_RESULTS+=("$stt_provider|$tts_provider|$sample|$elapsed_raw|$wer")
    done
  done
done

echo ""

# ============================================================================
# Summary Statistics
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "STT Times (avg,p50,p95,min,max):"
whisper_times=()
vosk_times=()
whisper_wers=()
vosk_wers=()

for r in "${STT_RESULTS[@]}"; do
  provider=$(echo "$r" | cut -d'|' -f1)
  time=$(echo "$r" | cut -d'|' -f3)
  w=$(echo "$r" | cut -d'|' -f4)
  if [ "$provider" = "whisper_cpp" ]; then
    whisper_times+=("$time")
    whisper_wers+=("$w")
  elif [ "$provider" = "vosk" ]; then
    vosk_times+=("$time")
    vosk_wers+=("$w")
  fi
done

if [ ${#whisper_times[@]} -gt 0 ]; then
  s=$(_stats "${whisper_times[@]}")
  echo "  whisper_cpp: $s"
  w=$(_stats "${whisper_wers[@]}")
  echo "    WER:       $w"
fi
if [ ${#vosk_times[@]} -gt 0 ]; then
  s=$(_stats "${vosk_times[@]}")
  echo "  vosk:        $s"
  w=$(_stats "${vosk_wers[@]}")
  echo "    WER:       $w"
fi

echo ""
echo "TTS Times (avg,p50,p95,min,max):"
piper_times=()
espeak_times=()
for r in "${TTS_RESULTS[@]}"; do
  provider=$(echo "$r" | cut -d'|' -f1)
  time=$(echo "$r" | cut -d'|' -f4)
  if [ "$provider" = "piper" ]; then
    piper_times+=("$time")
  elif [ "$provider" = "espeak" ]; then
    espeak_times+=("$time")
  fi
done
if [ ${#piper_times[@]} -gt 0 ]; then
  s=$(_stats "${piper_times[@]}")
  echo "  piper:  $s"
fi
if [ ${#espeak_times[@]} -gt 0 ]; then
  s=$(_stats "${espeak_times[@]}")
  echo "  espeak: $s"
fi

echo ""
echo "CSV written: $OUT_CSV"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Benchmark completed                                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
