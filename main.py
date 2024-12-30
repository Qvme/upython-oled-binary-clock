import machine
import ssd1306
import network
import ntptime
import time

# find out offset for your loc here >> https://en.wikipedia.org/wiki/List_of_UTC_offsets
OFFSET=5*60*60+30*60  # for IST timezone
DISPLAY_IMAGE_PATH="array3.txt" #checkout this for more.
CONFIG_PATH="config.conf"

oled_width=128
oled_height=64
rad=7 #rad >> curvature value for round corners(only topRight & bottomLeft) on boarder
#Sqaure-bit coordinates(x,y,w,h)
hh_blocks = [
                (40,20,10,10), (52,20,10,10),
                (64,20,10,10), (76,20,10,10)
            ] 
mm_blocks = [
                (28, 35, 10, 10), (40, 35, 10, 10),
                (52, 35, 10, 10), (64, 35, 10, 10),
                (76, 35, 10, 10), (88, 35, 10, 10)
            ]
ss_blocks = [
                (28, 49, 10, 10), (40, 49, 10, 10),
                (52, 49, 10, 10), (64, 49, 10, 10),
                (76, 49, 10, 10), (88, 49, 10, 10)
            ]

def readConfig(file):
    """
    reads config file and formats it output in key-val pair
    """
    try:
        config={}
        with open(file,"r") as file:
            for line in file:
                line.strip()
                if line and not line.startswith("#"):
                    key, val = line.split("=", 1)
                    config[key.strip('"')] = val.strip('"')
    except FileNotFoundError:
        oled.text(f"file missing." ,5, 5, 1)
        oled.text(f"repair", 5, 15, 1)
        oled.text("asap", 5, 25, 1)
        oled.show()
        oled.fill(0)
        print("config file not found :(( ")
    except Exception as e:
        print(f"an error occured as {e}")
    finally:
        return config

def configPass(config):
    """
    filters outs ssid-pass pairs from config dict returned by readConfig() func
    """
    ssid_pass={}
    for key,val in config.items():
        if key[:4]=="SSID":
            ssid_pass[val.strip("\n")] = config[f"PWD{key[4:]}"].strip("\n")
                
    return ssid_pass


# Connect to Wi-Fi
def conwifi(ssid_pass, wlan=network.WLAN(network.STA_IF)):
    """
    recursively checks out available wifi network,
    using available ssid ,pass from config.conf
    """
    wlan.active(True)
    for ssid, pwd in ssid_pass.items():
        try:
            cnt=0
            wlan.connect(ssid, pwd)
            while not wlan.isconnected():
                time.sleep(1)
                cnt +=1
                if cnt>4:
                    print(f"couldn't connect to {ssid}\ntrying next...")
                    oled.text(f"conn fail." ,5, 5, 1)
                    oled.text(f"{ssid}", 5, 15, 1)
                    oled.text("trying next...", 5, 25, 1)
                    oled.show()
                    oled.fill(0)
                    break
            if wlan.isconnected():
                print(f"connected to {ssid}")
                oled.text(f"conn succ." ,5, 5, 1)
                oled.text(f"{ssid}", 5, 15, 1)
                oled.show()
                time.sleep(1)
                oled.fill(0)
                
                break
        except Exception as e:
            print(f"An error occurred while connecting to {ssid}: {e}")

def syncUTCtime():
    """
    fetches UTC time values using network time protocol module
    """
    try:
        ntptime.settime() #syncs with UTC
        oled.text(f"sync successfull.." ,5, 5, 1)
        oled.show()
        time.sleep(1)
        oled.fill(0)
        print('Time synchronized with NTP server.')
    except Exception as e:
        oled.text(f"failed to sync." ,5, 5, 1)
        oled.show()
        time.sleep(1)
        oled.fill(0)
        print('Failed to synchronize time:', e)




def draw_square(x, y, height ,width, fill):
    """
    x, y cords of top left vertex ,height width as usual,
    fill val 1 for white, o for black
    """

    if x>128 or x<0 or y<0 or y>64:
        return "error, out of range index"
    if x+width>128 or y+height>64:
        return "square is going out of display"

    for ycord in range (y, y+height):
        for xcord in range(x,x+width):
            oled.pixel(xcord, ycord,fill)
    
def init_oled(sclPin=5, sdaPin=4, oled_width=128, oled_height=64):
    """
    intialises oled display, and borders
    sclPin, sdaPin GPIOs for I2C communication
    oled_width, oled height dimensions of oled display
    
    """
    i2c = machine.SoftI2C(scl=machine.Pin(sclPin), sda=machine.Pin(sdaPin))
    oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
    oled.fill(0)

    
    return oled

def add_boarders():
    """
    styling with boarders, and curved corners 
    """
    lenHori ,lenVert = oled_width-1 ,oled_height-1 #for compatibility with frambuff funcs
    oled.hline(0,0,lenHori-rad,1)
    oled.hline(rad,lenVert,lenHori,1)
    oled.vline(0,0,lenVert-rad,1)
    oled.vline(lenHori,rad,lenVert,1)
    oled.ellipse(lenHori-rad,rad,rad,rad,1,False,1)
    oled.ellipse(rad,lenVert-rad, rad,rad,1,False,4)
    oled.show()
    


def set_time(time_str):
    """
    Input string with format "hh:mm:ss"
    """
    time_tup = time_str.split(":")
    hh, mm, ss = (int(i) for i in time_tup)
    # Determine if it's day or night
    isday = 6 <= hh < 18
    isnight = not isday
    # Convert to 12-hour format for display
    if hh > 12:
        hh = hh - 12

    # Convert to binary strings
    hh_bin = f"{hh:04b}"
    mm_bin = f"{mm:06b}"
    ss_bin = f"{ss:06b}"
     
    for index,(state) in enumerate(hh_bin):
        draw_square(*(int(x) for x in hh_blocks[index]),int(state))
    
    for index, (state) in enumerate(mm_bin):
        draw_square(*(int(x) for x in mm_blocks[index]), int(state))
    
    for index, (state) in enumerate(ss_bin):
        draw_square(*(int(x) for x in ss_blocks[index]), int(state))
    
    return isday
def set_pixels_from_file(filename):
    """
    sets image from textfile pixel by pixel on oled for more ref docs
    """
    with open(filename, 'r') as file:
        for y, line in enumerate(file):
            line = line.strip()
            if y < oled_height:
                for x in range(len(line)):
                    state = int(line[x])
                    oled.pixel(x, y, state)
    
    #little blink thing
    for i in range(3):
        oled.invert(False)
        oled.show()
        time.sleep(0.3)
        oled.invert(True)
        oled.show()
        time.sleep(0.3)
    oled.invert(False)
    oled.fill(0)
    
def preview_animation():
    """
    some fancy startup thing, nothing much..
    """
    msg="System boot initiated. Loading core components. Initializing... Authentication protocols online, security checks in progress. Welcome to the interface".split()
    for i in msg:
        oled.text(i, 10 ,30, 1)
        oled.show()
        oled.fill(0)
        time.sleep(0.1)
    for i in range(2):
        for i in range(0,127,2):
            oled.vline(i,0,63,1)
            oled.show()
        oled.fill(0)
        for i in range(0,63,2):
            oled.hline(0,i,127,1)
            oled.show()
        oled.fill(0)
        for i in reversed(range(0, 63,2)):
            oled.hline(0,i,127,1)
            oled.show()
        oled.fill(0)
        for i in reversed(range(0, 127,2)):
            oled.vline(i,0,127,1)
            oled.show()
        oled.fill(0)
    set_pixels_from_file(DISPLAY_IMAGE_PATH)

def main():
    global oled
    oled = init_oled()
    oled.show()
    preview_animation()
    config = readConfig(CONFIG_PATH)
    ssid_pass = configPass(config)
    conwifi(ssid_pass)
    syncUTCtime()
    add_boarders()
    
    while True:
        # Get the current time
        current_time = time.localtime(time.time()+OFFSET)
        #print('\rCurrent time:', current_time[3], current_time[4], current_time[5])
        day = set_time(f"{current_time[3]}:{current_time[4]}:{current_time[5]}")
        if not day:
            draw_square(100,11,5,5,0) # to clear if it was day earlier
            oled.text("night",60,10)
            draw_square(105,11,5,5,1)
            
        else:
            draw_square(105,11,5,5,0) # to clear if it was night earlier
            oled.text("day",70,10)
            draw_square(100,11,5,5,1)
        
        time.sleep(0.5)
        oled.show()

if __name__ == "__main__":
    main()

