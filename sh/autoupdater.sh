while true
do
  git fetch;
  LOCAL=$(git rev-parse HEAD);
  REMOTE=$(git rev-parse @{u});

  # If our local revision id doesn't match the remote, we will need to pull the changes
  if [ "{$LOCAL}" != "{$REMOTE}" ]; then
    echo An update has been noticed

    echo Killing Python
    pkill python # Maybe we should kill only lotus.py...

    # pull and merge changes
    echo Pulling changes
    git pull origin master;

    echo Starting lotus.py
    nohup python3.7 lotus.py &

  fi
  sleep 5
done