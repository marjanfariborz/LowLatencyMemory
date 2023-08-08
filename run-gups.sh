#iso bw
for num_chnls in 8 16 32
    do
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp1/chnls_$num_chnls/LLM/ configs-gups-llm/run_llm_gups.py 64 LLM $num_chnls 1000 &
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp1/chnls_$num_chnls/FGDRAM/ configs-gups-llm/run_llm_gups.py 64 FGDRAM $num_chnls 1000 &
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp1/chnls_$num_chnls/HBMSALP/ configs-gups-llm/run_llm_gups.py 64 HBMSALP $num_chnls 1000 &
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp1/chnls_$num_chnls/HBM/ configs-gups-llm/run_llm_gups.py 64 HBM $num_chnls 1000 &
done
#iso capacity
for num_cores in 16 32 64 128
    do for num_chnls in 8 16 32
        do
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp2/cores_$num_cores/chnls_$num_chnls/LLM/ configs-gups-llm/run_llm_gups.py $num_cores LLM $num_chnls 1000 &
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp2/cores_$num_cores/chnls_$num_chnls/FGDRAM/ configs-gups-llm/run_llm_gups.py $num_cores FGDRAM $(($num_chnls * 2)) 1000 &
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp2/cores_$num_cores/chnls_$num_chnls/HBMSALP/ configs-gups-llm/run_llm_gups.py $num_cores HBMSALP $(($num_chnls * 8)) 1000 &
        gem5/build/NULL/gem5.opt -re --outdir=results-gups-exp2/cores_$num_cores/chnls_$num_chnls/HBM/ configs-gups-llm/run_llm_gups.py $num_cores HBM $(($num_chnls * 8)) 1000 &
    done
done

