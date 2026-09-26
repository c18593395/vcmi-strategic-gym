# duel 局统计脚本（只读分析 108X108_02_duel 收口判据）
# 用法: awk -f duel_stat.awk <duel_SLOT行列表文件>
# 提取字段: step / avg_r / nsteps / rc，按出现顺序分前1/3、后1/3
match($0,/step[0-9]+/){s=substr($0,RSTART+5,RLENGTH-5)}
match($0,/avg_r=[-0-9.]+/){a=substr($0,RSTART+7,RLENGTH-7)}
match($0,/nsteps=[0-9]+/){n=substr($0,RSTART+7,RLENGTH-7)}
match($0,/rc=[0-9]+/){rc=substr($0,RSTART+3,RLENGTH-3)}
{
  N++; steps[N]=s; avs[N]=a; ns[N]=n; rcs[N]=rc; sum+=a;
  if(a+0>0) pos++;
  if(n+0==250) full++;
  if(rc!="0") bad++;
}
END{
  third=int(N/3);
  s1=0; s3=0; c1=0; c3=0;
  for(i=1;i<=N;i++){
    if(i<=third){s1+=avs[i]; c1++}
    else if(i>2*third){s3+=avs[i]; c3++}
  }
  m1=(c1?s1/c1:0); m3=(c3?s3/c3:0);
  ratio=(c1>0 && m1!=0)?m3/m1:-1;
  printf "N=%d overall_avg_r=%.3f first_third_avg=%.3f last_third_avg=%.3f ratio_last_vs_first=%.3f\n", N, sum/N, m1, m3, ratio;
  printf "full250=%d full_pct=%.1f pos_gt0=%d pos_pct=%.1f rc0=%d rc_bad=%d\n", full, 100*full/N, pos+0, 100*(pos+0)/N, N-bad, bad+0;
}
