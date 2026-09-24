set pagination off
set confirm off
set breakpoint pending on
break CVCMIServer::setState if value == 2
commands $bpnum
silent
printf "\n===== KILLER HIT setState(SHUTDOWN) =====\n"
bt 30
echo \n----- ALL THREADS -----\n
thread apply all bt 12
kill
quit
end
run
