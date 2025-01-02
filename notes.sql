SELECT answer
FROM answers
LEFT JOIN definitions ON answers.answer = word
WHERE ((definitions.word IS NULL) OR (FALSE))
ORDER BY answer;

COALESCE(substr( definitions.definition, 1, 10), '') 

SELECT answers.*,COALESCE(substr( definitions.definition, 1, 10), '')
FROM answers
LEFT JOIN definitions ON answers.answer = word
WHERE definitions.definition IS NULL;

SELECT answers.answer
FROM answers
LEFT JOIN definitions ON answers.answer = word
WHERE definitions.definition IS NULL
ORDER BY answers.answer;


HETZNER
adduser sjf
sudo adduser sjf sudo
timedatectl set-timezone America/Los_Angeles

apt-get update
apt-get install git npm
npm install -D tailwindcss

# install sjf public ssh key
...
# Create new ssh private key
ssh-keygen -t ed25519 -C "sjf@me.com"
# Add to github
open https://github.com/settings/ssh/new


------

docker run -d \
  --name foo \
  -v www:/var/www/html:ro \
  -p 80:80 \
  rtsp/lighttpd

  find /path/to/directory


find . -name ._\* -type f -mmin +180 | xargs rm


