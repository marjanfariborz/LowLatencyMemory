#iso bw
for bw in 8 16 24 32 40 48 56 64 72 80 88 96 104 112 120 128
    do for traffic in STRIDED RANDOM
        do for rd_perc in 100 80
            do
            gem5/build/NULL/gem5.opt --outdir=synth-results/results-synthetic-exp1/LLM/MODE_$traffic/bw_$bw/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 LLM 32 256 10us $bw $rd_perc 0 &
            gem5/build/NULL/gem5.opt --outdir=synth-results/results-synthetic-exp1/HBM/MODE_$traffic/bw_$bw/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 HBM 256 256 10us $bw $rd_perc 0 &
            gem5/build/NULL/gem5.opt --outdir=synth-results/results-synthetic-exp1/HBMSALP/MODE_$traffic/bw_$bw/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 HBMSALP 256 256 10us $bw $rd_perc 0 &
            gem5/build/NULL/gem5.opt --outdir=synth-results/results-synthetic-exp1/FGDRAM/MODE_$traffic/bw_$bw/RD_$rd_perc -re configs-synth-llm//run_llm_eval.py $traffic 32 FGDRAM 64 256 10us $bw $rd_perc 0 &
        done
    done
done

#iso capcity
for channel in 32 128 64 256
    do for traffic in RANDOM STRIDED
        do for rd_perc in 100 80
            do
            gem5/build/NULL/gem5.opt --outdir=results-synthetic-exp2/LLM/MODE_$traffic/channel_$channel/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 LLM $channel 10us $(($channel*4)) $rd_perc 0 &
            gem5/build/NULL/gem5.opt --outdir=results-synthetic-exp2/HBM/MODE_$traffic/channel_$channel/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 HBM $channel 10us $(($channel/2)) $rd_perc 0 &
            gem5/build/NULL/gem5.opt --outdir=results-synthetic-exp2/HBMSALP/MODE_$traffic/channel_$channel/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 HBMSALP $channel 10us $(($channel/2)) $rd_perc 0 &
            gem5/build/NULL/gem5.opt --outdir=results-synthetic-exp2/FGDRAM/MODE_$traffic/channel_$channel/RD_$rd_perc -re configs-synth-llm/run_llm_eval.py $traffic 32 FGDRAM $channel 10us $(($channel * 2)) $rd_perc 0 &
        done
    done
done