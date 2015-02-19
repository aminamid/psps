echo search01 1:*
./imap.py -p 60143 '1:* NOT DELETED'
echo search02 1:*
./imap.py -p 60143 '1:* UNSEEN UNDELETED'
echo search03 1:*
./imap.py -p 60143 '1:* DELETED'
echo search04 1:*
./imap.py -p 60143 '1:* NOT DELETED' '1:* NOT DELETED'

echo search01 None
./imap.py -p 60143 'NOT DELETED'
echo search02 None
./imap.py -p 60143 'UNSEEN UNDELETED'
echo search03 None
./imap.py -p 60143 'DELETED'
echo search04 None
./imap.py -p 60143 'NOT DELETED' 'NOT DELETED'

