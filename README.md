# MiBand2
Library to work with Xiaomi MiBand 2 (Support python2/python3)
[Read the Article here](https://medium.com/@a.nikishaev/how-i-hacked-xiaomi-miband-2-to-control-it-from-linux-a5bd2f36d3ad)

# Contributors & Info Sources
1) Base lib provided by [Leo Soares](https://github.com/leojrfs/miband2)
2) Additional debug & fixes was made by my friend [Volodymyr Shymanskyy](https://github.com/vshymanskyy/miband2-python-test)
3) Some info that really helped i got from [Freeyourgadget team](https://github.com/Freeyourgadget/Gadgetbridge/tree/master/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/huami/miband2)

## Interesting stuff
[More interesing stuff about Software Developing](http://t.me/devs_world)

# Run 

1) Install dependencies
```sh
pip install -r requirements.txt
```
2) Turn on your Bluetooth
3) Unpair you MiBand2 from current mobile apps
4) Find out you MiBand2 MAC address
```sh
sudo hcitool lescan
```
5) Run this to auth device
```sh
python example.py --mac MAC_ADDRESS --init
```
6) Run this to call demo functions
```sh
python example.py --standard --mac MAC_ADDRESS
python example.py --help
```
7) If you having problems(BLE can glitch sometimes) try this and repeat from 4)
```sh
sudo hciconfig hci0 reset
```
Also there is cool JS library that made Volodymyr Shymansky https://github.com/vshymanskyy/miband-js

# Donate
If you like what im doing, you can send me some money for pepsi(i dont drink alcohol). https://patreon.com/mlworld

<p xmlns:dct="http://purl.org/dc/terms/">
  <a rel="license"
     href="http://creativecommons.org/publicdomain/zero/1.0/">
    <img src="http://i.creativecommons.org/p/zero/1.0/88x31.png" style="border-style: none;" alt="CC0" />
  </a>
  <br />
  To the extent possible under law,
  <a rel="dct:publisher"
     href="http://medium.com/@a.nikishaev">
    <span property="dct:title">Andrey Nikishaev</span></a>
  has waived all copyright and related or neighboring rights to
  <span property="dct:title">Library to work with Xiaomi MiBand 2 </span>.
</p>
