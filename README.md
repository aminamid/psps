
```
$ imap.py -p 60143  '1:* NOT DELETED'
2015/02/17T13:22:45.370 OK:connect    127.0.0.1 60143         :          2
2015/02/17T13:22:45.372 OK:capability                         :          1
2015/02/17T13:22:45.403 OK:login      el00 el00               :         31
2015/02/17T13:22:45.569 OK:select     INBOX                   :        165
2015/02/17T13:22:45.894 OK:uid-SEARCH 1:* NOT DELETED         :        325
2015/02/17T13:22:45.912 OK:logout                             :         17

$ imap.py -p 60143  '1:* NOT DELETED' '1:* NOT DELETED'
2015/02/17T13:22:57.873 OK:connect    127.0.0.1 60143         :          2
2015/02/17T13:22:57.874 OK:capability                         :          0
2015/02/17T13:22:57.899 OK:login      el00 el00               :         24
2015/02/17T13:22:58.037 OK:select     INBOX                   :        137
2015/02/17T13:22:58.353 OK:uid-SEARCH 1:* NOT DELETED         :        316
2015/02/17T13:22:58.563 OK:uid-SEARCH 1:* NOT DELETED         :        209
2015/02/17T13:22:58.582 OK:logout                             :         19

$ imap.py -p 60143  '1:* NOT DELETED' '1:* NOT DELETED' '1000:* NOT DELETED'
2015/02/17T13:23:18.040 OK:connect    127.0.0.1 60143         :          2
2015/02/17T13:23:18.041 OK:capability                         :          1
2015/02/17T13:23:18.072 OK:login      el00 el00               :         30
2015/02/17T13:23:18.215 OK:select     INBOX                   :        142
2015/02/17T13:23:18.529 OK:uid-SEARCH 1:* NOT DELETED         :        314
2015/02/17T13:23:18.759 OK:uid-SEARCH 1:* NOT DELETED         :        229
2015/02/17T13:23:18.956 OK:uid-SEARCH 1000:* NOT DELETED      :        196
```
