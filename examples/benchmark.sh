#!/usr/bin/env bash
# Benchmark STT and TTS providers - timing and accuracy matrix
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STTS="$ROOT/python/stts"
SAMPLES="$ROOT/python/samples"
VENV="$ROOT/venv/bin/python"
TMP_DIR="/tmp/stts_benchmark_$$"

# Use venv python if available
if [ -f "$VENV" ]; then
  PYTHON="$VENV"
else
  PYTHON="python3"
fi

mkdir -p "$TMP_DIR"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

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

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  STT Benchmark${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

printf "%-15s %-20s %-10s %-15s %-20s\n" "Provider" "Sample" "Time(s)" "Accuracy" "Transcription"
echo "─────────────────────────────────────────────────────────────────────────────────"

STT_RESULTS=()

for i in "${!STT_PROVIDERS[@]}"; do
  provider="${STT_PROVIDERS[$i]}"
  model="${STT_MODELS[$i]}"
  
  for sample in "${!SAMPLES_EXPECTED[@]}"; do
    expected="${SAMPLES_EXPECTED[$sample]}"
    sample_path="$SAMPLES/$sample"
    
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
    start_time=$(date +%s.%N)
    result=$(eval "$cmd" 2>/dev/null | tail -1) || result=""
    end_time=$(date +%s.%N)
    
    elapsed=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
    elapsed=$(printf "%.2f" "$elapsed")
    
    # Calculate accuracy (simple word match)
    result_lower=$(echo "$result" | tr '[:upper:]' '[:lower:]')
    expected_lower=$(echo "$expected" | tr '[:upper:]' '[:lower:]')
    
    if [ "$result_lower" = "$expected_lower" ]; then
      accuracy="100%"
      acc_color="$GREEN"
    elif echo "$result_lower" | grep -q "$(echo "$expected_lower" | cut -d' ' -f1)"; then
      accuracy="~50%"
      acc_color="$YELLOW"
    else
      accuracy="0%"
      acc_color="$RED"
    fi
    
    # Truncate result for display
    result_display="${result:0:18}"
    if [ ${#result} -gt 18 ]; then
      result_display="${result_display}..."
    fi
    
    printf "%-15s %-20s %-10s ${acc_color}%-15s${NC} %-20s\n" \
      "$provider" "${sample%.wav}" "${elapsed}s" "$accuracy" "$result_display"
    
    STT_RESULTS+=("$provider|$sample|$elapsed|$accuracy|$result")
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
    start_time=$(date +%s.%N)
    STTS_TTS_PROVIDER="$provider" STTS_TTS_VOICE="$voice" \
      $PYTHON $STTS --tts-test "$phrase" >/dev/null 2>&1 || true
    end_time=$(date +%s.%N)
    
    elapsed=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
    elapsed=$(printf "%.2f" "$elapsed")
    
    # Truncate phrase for display
    phrase_display="${phrase:0:38}"
    if [ ${#phrase} -gt 38 ]; then
      phrase_display="${phrase_display}..."
    fi
    
    printf "%-15s %-10s %-40s %-10s\n" \
      "$provider" "$voice" "$phrase_display" "${elapsed}s"
    
    TTS_RESULTS+=("$provider|$voice|$phrase|$elapsed")
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

printf "%-15s %-15s %-20s %-12s %-15s\n" "STT" "TTS" "Sample" "Total(s)" "Status"
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
      start_time=$(date +%s.%N)
      
      # Step 1: STT
      transcription=$(eval "$stt_cmd" 2>/dev/null | tail -1) || transcription=""
      
      # Step 2: TTS (speak transcription)
      if [ -n "$transcription" ]; then
        STTS_TTS_PROVIDER="$tts_provider" STTS_TTS_VOICE="$tts_voice" \
          $PYTHON $STTS --tts-test "$transcription" >/dev/null 2>&1 || true
        status="${GREEN}✅ OK${NC}"
      else
        status="${RED}❌ FAIL${NC}"
      fi
      
      end_time=$(date +%s.%N)
      elapsed=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "0")
      elapsed=$(printf "%.2f" "$elapsed")
      
      printf "%-15s %-15s %-20s %-12s " \
        "$stt_provider" "$tts_provider" "${sample%.wav}" "${elapsed}s"
      echo -e "$status"
      
      PIPELINE_RESULTS+=("$stt_provider|$tts_provider|$sample|$elapsed")
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

# Calculate averages
whisper_total=0
whisper_count=0
vosk_total=0
vosk_count=0
piper_total=0
piper_count=0
espeak_total=0
espeak_count=0

for r in "${STT_RESULTS[@]}"; do
  provider=$(echo "$r" | cut -d'|' -f1)
  time=$(echo "$r" | cut -d'|' -f3)
  
  if [ "$provider" = "whisper_cpp" ]; then
    whisper_total=$(echo "$whisper_total + $time" | bc 2>/dev/null || echo "$whisper_total")
    ((whisper_count++)) || true
  elif [ "$provider" = "vosk" ]; then
    vosk_total=$(echo "$vosk_total + $time" | bc 2>/dev/null || echo "$vosk_total")
    ((vosk_count++)) || true
  fi
done

for r in "${TTS_RESULTS[@]}"; do
  provider=$(echo "$r" | cut -d'|' -f1)
  time=$(echo "$r" | cut -d'|' -f4)
  
  if [ "$provider" = "piper" ]; then
    piper_total=$(echo "$piper_total + $time" | bc 2>/dev/null || echo "$piper_total")
    ((piper_count++)) || true
  elif [ "$provider" = "espeak" ]; then
    espeak_total=$(echo "$espeak_total + $time" | bc 2>/dev/null || echo "$espeak_total")
    ((espeak_count++)) || true
  fi
done

echo "STT Average Times:"
if [ "$whisper_count" -gt 0 ]; then
  avg=$(echo "scale=2; $whisper_total / $whisper_count" | bc 2>/dev/null || echo "N/A")
  echo "  whisper_cpp: ${avg}s"
fi
if [ "$vosk_count" -gt 0 ]; then
  avg=$(echo "scale=2; $vosk_total / $vosk_count" | bc 2>/dev/null || echo "N/A")
  echo "  vosk:        ${avg}s"
fi

echo ""
echo "TTS Average Times:"
if [ "$piper_count" -gt 0 ]; then
  avg=$(echo "scale=2; $piper_total / $piper_count" | bc 2>/dev/null || echo "N/A")
  echo "  piper:  ${avg}s"
fi
if [ "$espeak_count" -gt 0 ]; then
  avg=$(echo "scale=2; $espeak_total / $espeak_count" | bc 2>/dev/null || echo "N/A")
  echo "  espeak: ${avg}s"
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Benchmark completed                                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
