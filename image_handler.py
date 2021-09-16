"""
    Common processing functions for grayscale images: (x, y), where x,y in range (0,255)
"""

def auto_contrast(im_array):
    """ Rescale the image intensity levels to a reasonable range using the top/bottom 2 percent
        of the data to define the intensity levels
    """
    import numpy as np
    ## avoid hotspot pixels by looking at a group of pixels at the extreme ends of the image
    minval = np.percentile(im_array, 2)
    maxval = np.percentile(im_array, 98)
    ## remove pixles above/below the defined limits
    im_array = np.clip(im_array, minval, maxval)
    ## rescale the image into the range 0 - 255
    im_array = ((im_array - minval) / (maxval - minval)) * 255

    return im_array

def sigma_contrast(im_array, sigma):
    """ Rescale the image intensity levels to a range defined by a sigma value (the # of
        standard deviations to keep). Can perform better than auto_contrast when there is
        a lot of dark pixels throwing off the level balancing.
    """
    import numpy as np
    stdev = np.std(im_array)
    mean = np.mean(im_array)
    print("Image intensity data (mean, stdev) = (%s, %s)" % (mean, stdev))
    minval = mean - (stdev * sigma)
    maxval = mean + (stdev * sigma)
    ## remove pixles above/below the defined limits
    im_array = np.clip(im_array, minval, maxval)
    ## rescale the image into the range 0 - 255
    im_array = ((im_array - minval) / (maxval - minval)) * 255

    return im_array

def whiten_outliers(im_array, min, max):
    """ Set any pixels outside of a defined intensity range to 255 (white)
    """
    import numpy as np
    ## use the input mean/max to clip the image before increasing contrast
    im_array = np.where(im_array < min, 255, im_array)
    im_array = np.where(im_array > max, 255, im_array)
    return im_array

def extract_boxes(im_array, box_size, coords, DEBUG = True):
    """
    PARAMETERS
        im_array = np array (0 - 255)
        box_size = int(); pixel size of the box to extract
        coords = list( tuple(x, y), ... ); centered coordinates in pixels (top left == 0,0 by convention)
    RETURNS
        extracted_imgs = list( np arrays of dimension box_size , ... )
    """
    extracted_imgs = []
    ## sanity check that not too many coordinates are being asked to be extracted
    if len(coords) > 500:
        print(" ERROR :: extracted_boxes is capped at 500 coordinates to avoid memory issues, remove some and re-run")
        return extracted_imgs

    box_size_halfwidth = int( box_size / 2)

    for coordinate in coords:
        x0 = coordinate[0] - box_size_halfwidth
        y0 = coordinate[1] - box_size_halfwidth
        x1 = coordinate[0] + box_size_halfwidth
        y1 = coordinate[1] + box_size_halfwidth

        extracted_img = im_array[y0:y1,x0:x1]
        extracted_imgs.append(extracted_img)

    if DEBUG:
        print(" Extracted %s boxes from image" % len(extracted_imgs))

    return extracted_imgs

def find_intensity_range(im_arrays, DEBUG = True):
    """
        im_arrays = list( 2d numpy arrays, ...)

    RETURNS:
        min = int()
        max = int()
    """
    import numpy as np
    import statistics
    mins = []
    maxs = []
    ## get the min/max value for each image we are loading
    for im_array in im_arrays:
        mins.append(np.min(im_array))
        maxs.append(np.max(im_array))
    ## get the mean value for the min/maxes
    min = int(statistics.mean(mins))
    max = int(statistics.mean(maxs))
    if DEBUG:
        print(" find_intensity_range :: %s imgs" % len(im_arrays))
        print("    ... (min, max) = (%s, %s)" % (min, max))
    return (min, max)

def gaussian_blur(im_array, sigma):
    import scipy.ndimage as ndimage

    blurred_img = ndimage.gaussian_filter(im_array, sigma)
    return blurred_img

def image2array(file, DEBUG = True):
    """
        Import an image into a grayscal 2d numpy array with values from (0 - 255), where
            0 == black
            255 == white
    """
    from PIL import Image as PIL_Image
    import numpy as np

    im = PIL_Image.open(file).convert('L') # 'L' == convert to grayscale data
    # convert image to numpy array
    im_data = np.asarray(im)

    if DEBUG:
        print("===================================================")
        print(" IMPORT IMAGE :: %s" % file)
        print("===================================================")
        print("   >> %s px, min = %s, max = %s" % (im_data.shape, np.min(im_data), np.max(im_data)))

    return im_data

def display_img(im_array, coords = None, box_size = 1):
    """
        box_size = int(); pixel size of the particle
    """
    from PIL import Image as PIL_Image
    from PIL import ImageTk

    box_size_halfwidth = int( box_size / 2 )

    root = Tk()
    canvas = Canvas(root, width = im_array.shape[0], height = im_array.shape[1])
    canvas.pack()
    img = PIL_Image.fromarray(im_array)
    img = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=NW, image=img)

    if coords != None:
        for coordinate in coords:
            # break
            ## each coordinate is the center of a box, thus we need to offset by half the gif_box_width pixel length to get the bottom left and top right of the rectangle
            x0 = coordinate[0] - box_size_halfwidth
            y0 = coordinate[1] - box_size_halfwidth
            x1 = coordinate[0] + box_size_halfwidth
            y1 = coordinate[1] + box_size_halfwidth #y0 - img_box_size # invert direction of box to take into account x0,y0 are at bottom left, not top left
            canvas.create_rectangle(x0, y0, x1, y1, outline='red', width=1, tags='particle_positions')

    root.mainloop()

def gaussian_disk(size):
    """ Creates a soft gaussian grayscale image of given pixel size with values in range 0 -- 255
    """
    import numpy as np

    size = int(size)
    x, y = np.meshgrid(np.linspace(-1,1, size), np.linspace(-1,1, size))
    d = np.sqrt(x*x+y*y)
    sigma, mu = 0.4, 0.0
    g = np.exp(-( (d-mu)**2 / ( 2.0 * sigma**2 ) ) )
    ## invert color to we match to dark pixels
    g = 1 - g

    g = g * 255
    return g

def template_cross_correlate(im_array, template, threshold, DEBUG = False):
    """
    PARAMETERS
        im_array = np array of grayscale img in range 0 - 255
        template = np array of grayscale template img in range 0 - 255
        threshold = int(); peak cutoff in range 0 - 1
    RETURNS
        cc = cross correlation image as a grayscale (0 - 255), note peaks represent positions aligned with top-right of template!
    """
    import numpy as np
    from scipy import signal

    if DEBUG:
        print("Template info: %s, min = %s, max %s" % (template.shape, np.min(template), np.max(template)))
    cc = signal.correlate2d(im_array, template, boundary='symm', mode='same')
    ## determine the threshold at which to keep peaks
    cc_min, cc_max = (np.min(cc), np.max(cc))
    cc_range = cc_max - cc_min
    cc_threshold_cutoff = cc_min + (threshold * cc_range)
    print("cc min, max, range, threshold value = (%s, %s, %s, %s)" % ( np.min(cc), np.max(cc), cc_range, cc_threshold_cutoff))
    ## remove signal below peaks
    cc = np.where(cc < cc_threshold_cutoff, 0, 255)
    return cc


# template = gaussian_disc(scaled_box_size)
# template -= template.mean() ## NOTE: maybe have the template scaled not by mean() but by the expected max signal of the picked particles so far?
#
# cc_data = template_cross_correlate(im_data, template)


def bool_img(im_array, threshold):
    import numpy as np
    im_array = np.where(im_array < threshold, 255, 0)
    return im_array


#############################################
##  RUN BLOCK
#############################################
if __name__ == "__main__":

    import sys, os
    from tkinter import *

    ## allow functions of this script to be tested by supplying in an image on the commandline via:
    ##      $ image_handler.py  <img name>
    fname = sys.argv[1]

    ## edit the functions that run in this block to test proper execution
    im = image2array(fname)

    ## box_size and some coordinates for img B1g1...Exp_10.jpg
    coords = [(444,138), (452, 124), (466, 117)]
    box_size = 17
    extracted_imgs = extract_boxes(im, box_size, coords, DEBUG = True)
    min, max = find_intensity_range(extracted_imgs)

    ## try to limit effect of noise by applying a soft blur to the img
    im = gaussian_blur(im, 1.5)

    im = whiten_outliers(im, min, max)

    ## TRY: instead of whitening outliers, take in a set of particle coordinates, determine their contrast (avgmin, avgmax), and choose a threshold midway between them to apply a boolean mask that could then be used for labeling...see how it works
    cutoff = min + 20 #int(max - min / 1000000) + min
    im = bool_img(im, cutoff)

    # im = auto_contrast(im)
    # im = sigma_contrast(im, 2)
    ## try adding a highpass filter (upwards of 500 ang?)


    # template = gaussian_disk(17)
    # threshold = 0.7
    # cc = template_cross_correlate(im, template, threshold, DEBUG = True)

    display_img(im)
