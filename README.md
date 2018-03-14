# bitboard

Bitboard is a decentralized anonymous imageboard. It is built on top of Bitmessage's [decentralized mailing lists.](https://bitmessage.org/wiki/Decentralized_Mailing_List)

To get started, you must download and setup [Bitmessage](https://bitmessage.org) then [enable API access](https://bitmessage.org/wiki/API_Reference#Enable_the_API). Bitmessage must be running in order for Bitboard to work. 

Once you have Bitmessage setup and running, you may download and run bitboard with the following commands.

    git clone https://github.com/michrob/bitboard
    cd bitboard/
    python2 -m pip install -r requirements.txt
    python2 bitboard.py
  
bitboard runs on port 8080 by default, so you should see it running when you visit http://localhost:8080 in your browser. For security purposes, you should probably disable javascript.
