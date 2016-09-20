# storm_shut

A script to administratively shut down an interface when a storm control event is written to /var/log/messages

Includes an optional hold-down timer to reactivate the interface after user-defined timer expiry
  Specify a time vaue in minutes if it's desirable for the interface to re-enable
  
The script calls the API via the local webserver so it's required to activate this via the CLI as follows

management api http-commands
   protocol http localhost
   no shutdown
