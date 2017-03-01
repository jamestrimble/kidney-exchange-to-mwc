NF==2 || $1=="-1" { print; next }
{ if (rand() < .33) print }
