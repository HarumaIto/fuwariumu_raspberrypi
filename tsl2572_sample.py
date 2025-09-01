import smbus
import logging

# loggingの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    i2c = smbus.SMBus(1)
except (FileNotFoundError, PermissionError) as e:
    logging.error(f"I2Cバスの初期化に失敗しました: {e}")
    i2c = None

#TSL2572 Register Set
TSL2572_ADR      = 0x39
TSL2572_COMMAND  = 0x80
TSL2572_TYPE_REP = 0x00
TSL2572_TYPE_INC = 0x20
TSL2572_ALSIFC   = 0x66

TSL2572_SAI   = 0x40
TSL2572_AIEN  = 0x10
TSL2572_WEN   = 0x80
TSL2572_AEN   = 0x02
TSL2572_PON   = 0x01

TSL2572_ENABLE   = 0x00
TSL2572_ATIME    = 0x01
TSL2572_WTIME    = 0x03
TSL2572_AILTL    = 0x04
TSL2572_AILTH    = 0x05
TSL2572_AIHTL    = 0x06
TSL2572_AIHTH    = 0x07
TSL2572_PRES     = 0x0C
TSL2572_CONFIG   = 0x0D
TSL2572_CONTROL  = 0x0F
TSL2572_ID       = 0x12
TSL2572_STATUS   = 0x13
TSL2572_C0DATA   = 0x14
TSL2572_C0DATAH  = 0x15
TSL2572_C1DATA   = 0x16
TSL2572_C1DATAH  = 0x17

#TSL2572 settings
ATIME = 0xC0
GAIN = 1.0

def initTSL2572() :
    if i2c is None:
        logging.error("I2Cバスが利用できません。")
        return -1
    try:
        if (getTSL2572reg(TSL2572_ID)!=[0x34]) :
            #check TSL2572 ID
            logging.error("TSL2572のIDが一致しません。")
            return -1
        setTSL2572reg(TSL2572_COMMAND | TSL2572_TYPE_INC | TSL2572_CONTROL,0x00)
        setTSL2572reg(TSL2572_COMMAND | TSL2572_TYPE_INC | TSL2572_CONFIG,0x00)
        setTSL2572reg(TSL2572_COMMAND | TSL2572_TYPE_INC | TSL2572_ATIME,ATIME)
        setTSL2572reg(TSL2572_COMMAND | TSL2572_TYPE_INC | TSL2572_ENABLE,TSL2572_AEN | TSL2572_PON)
        return 0
    except IOError as e:
        logging.error(f"TSL2572の初期化に失敗しました: {e}")
        return -1


def setTSL2572reg(reg,dat) :
    if i2c is None:
        logging.error("I2Cバスが利用できません。")
        return
    try:
        i2c.write_byte_data(TSL2572_ADR,reg,dat)
    except IOError as e:
        logging.error(f"レジスタ書き込みに失敗しました: {e}")


def getTSL2572reg(reg) :
    if i2c is None:
        logging.error("I2Cバスが利用できません。")
        return [-1] # Return a value that indicates error
    try:
        dat = i2c.read_i2c_block_data(TSL2572_ADR,TSL2572_COMMAND | TSL2572_TYPE_INC | reg,1)
        return dat
    except IOError as e:
        logging.error(f"レジスタ読み取りに失敗しました: {e}")
        return [-1]


def getTSL2572adc() :
    if i2c is None:
        logging.error("I2Cバスが利用できません。")
        return [0, 0]
    try:
        dat = i2c.read_i2c_block_data(TSL2572_ADR,TSL2572_COMMAND | TSL2572_TYPE_INC | TSL2572_C0DATA,4)
        adc0 = (dat[1] << 8) | dat[0]
        adc1 = (dat[3] << 8) | dat[2]
        return[adc0,adc1]
    except IOError as e:
        logging.error(f"ADCデータの読み取りに失敗しました: {e}")
        return [0, 0]


def readData() -> dict[str, float]:
    if (initTSL2572()!=0) :
        print("Failed. Check connection!!")
        return {"adc0": 0, "adc1": 0, "lux": 0}

    adc = getTSL2572adc()
    cpl = (2.73 * (256 - ATIME) * GAIN)/(60.0)
    if cpl == 0:
        logging.error("CPLが0になりました。ATIMEとGAINの設定を確認してください。")
        return {"adc0": adc[0], "adc1": adc[1], "lux": 0}
    lux1 = ((adc[0] * 1.00) - (adc[1] * 1.87)) / cpl
    lux2 = ((adc[0] * 0.63) - (adc[1] * 1.00)) / cpl
    lux = max(lux1, lux2, 0)
    return {"adc0": adc[0], "adc1": adc[1], "lux": lux}

def init():
    initTSL2572()

def main():
    data = readData()
    if data:
        print(f"lux: {data['lux']}")

if __name__ == '__main__':
    main()
