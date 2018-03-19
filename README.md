# MiBand2
Library to work with Xiaomi MiBand 2

# Contributors & Info Sources
1) Base lib provided by [Leo Soares](https://github.com/leojrfs/miband2)
2) Additional debug & fixes was made by my friend [Volodymyr Shymanskyy](https://github.com/vshymanskyy/miband2-python-test)
3) Some info that really helped i got from [Freeyourgadget team](https://github.com/Freeyourgadget/Gadgetbridge/tree/master/app/src/main/java/nodomain/freeyourgadget/gadgetbridge/service/devices/miband2)

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
5) Run example.py
This will auth device
```sh
python example.py MAC_ADDRESS init
```
This will run demo
```sh
python example.py MAC_ADDRESS
```
6) If you having problems(BLE can glitch sometimes) try this and repeat from 4)
```sh
sudo hciconfig hci0 reset
```

# Donate
If you like what im doing, you can send me some money for pepsi(i dont drink alcohol). https://www.paypal.me/creotiv
