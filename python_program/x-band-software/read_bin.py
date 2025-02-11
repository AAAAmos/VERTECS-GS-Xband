import numpy as np
import matplotlib.pyplot as plt
import glob
from astropy.io import fits
# files = glob.glob('C:/Users/verte/Documents/TVT_15_08_2024/optical/opt_frame_*.bin')
# files.sort(key=)
# print(files[-1])
# file = files[-1]
# file = 'C:/Users/verte/Documents/TVT_15_08_2024/optical/opt_frame_13_22_164027.bin'

files = glob.glob('./optical/opt_frame_*.bin')
files.sort(key=lambda x:int(x.split('/')[-1].split('_')[2].split('_')[0]))
# print(files[0].split('/')[-1])
file = files[-1]
# file = "C:/Users/verte/Documents/TVT_15_08_2024/optical/20241011132505.bin"
print(file)
data = np.fromfile(file,dtype=np.uint16)
image_array = data.reshape(3003,3008)
plt.ion()
plt.imshow(image_array,)
plt.colorbar()
plt.show()
# input()
hdu = fits.PrimaryHDU(image_array)
file_name = input("input file name or enter empty to exit\n")
if file_name != "":
    hdu.writeto(f'measurement/{file_name}.fits',overwrite=True)
    plt.savefig(f'measurement/{file_name}.png')