#!/usr/bin/env python3

## TO DO:
##  - Try adding a binning factor so the algorithm first bins the input image before picking, may help reduce noise?

""" A program to take in an image and return an predicted particle centroid positions
"""

####################################################
## DEFINITIONS
####################################################

def usage():
    print("========================================================================================================")
    print(" A script to find centroids of particles from a grayscale image:")
    print("    $ peak_finder.py  image.jpg")
    print(" Manually edit the variables in the script before running if desired")
    print("========================================================================================================")
    # print(" Optional flags: ")
    # print("     --h   :: print this usage")
    # print("========================================================================================================")
    sys.exit()

def read_input():
    global input_file
    ## if no entries are given, print usage and exit
    if len(sys.argv) == 1:
        usage()

    ## read all entries and check if the help flag is called at any point
    for n in range(len(sys.argv[1:])+1):
        # if the help flag is called, pring usage and exit
        if sys.argv[n] == '-h' or sys.argv[n] == '--help':
            usage()

    ## read all commandline arguments and adjust variables accordingly
    for n in range(len(sys.argv[1:])+1):
        # read input with '.csv' as the input file
        if os.path.splitext(sys.argv[n])[1] == '.gif':
            input_file = sys.argv[n]
            print(" Analysing image = %s" % input_file)
            # base_file_name = os.path.splitext(input_file_name)[0]
    return

def load_dependencies():
    """ Load all packages needed for this script to run using __import__ to make the packages globally accessible to all functions
        REF: https://stackoverflow.com/questions/11990556/how-to-make-global-imports-from-a-function
    """
    ## sys and os are built-in packages, if they fail to load then python install is completely wrong!
    globals()['sys'] = __import__('sys')
    globals()['os'] = __import__('os')

    try:
        globals()['imageio'] = __import__('imageio')
    except:
        print(" ERROR :: Failed to import 'imageio'. Try: pip install imageio")
        sys.exit()

    try:
        globals()['np'] = __import__('numpy') ## similar to: import numpy as np
    except:
        print(" ERROR :: Failed to import 'numpy'. Try: pip install numpy")
        sys.exit()

    try:
        globals()['scipy'] = __import__('scipy')
    except:
        print(" ERROR :: Failed to import 'scipy'. Try: pip install scipy")
        sys.exit()

    try:
        globals()['matplotlib'] = __import__('matplotlib')
    except:
        print(" ERROR :: Failed to import 'matplotlib.pyplot' module. Try: pip install matplotlib")
        sys.exit()

    try:
        globals()['skimage'] = __import__('skimage')
    except:
        print(" ERROR :: Failed to import 'skimage'. Try: pip install skimage")
        sys.exit()

    return

def image_to_array(file):
    im = imageio.imread(file)
    print("  >> image dimensions :: (x, y) ->", im.shape, ", color depth :: (min, max) -> (%s, %s)" %(np.min(im), np.max(im)))
    return im

def invert_image(im_array, color_depth = 255):
    inverted_im = color_depth - im_array
    return inverted_im

def display_image(im_array, fig_title = '') :
    plt.figure()
    plt.imshow(im_array, cmap="gray")
    plt.title(fig_title)
    plt.show()

def display_two_images(im1, im2, fig_title1 = '', fig_title2 = '', coords = None, radius_pixels = 2):
    from matplotlib import pyplot as plt

    fig, axes = plt.subplots(1, 2, sharex=True, sharey=True)
    ax = axes.ravel()
    ax[0].imshow(im1, cmap=plt.cm.gray)
    ax[0].axis('off')
    ax[0].set_title(fig_title1)

    ax[1].imshow(im2, cmap=plt.cm.gray)
    ax[1].axis('off')
    ax[1].set_title(fig_title2)

    if coords is not None:
        # ax[1].autoscale(False)
        # ax[1].plot(coords[:, 1], coords[:, 0], 'r.')

        for coord in coords :
            r = radius_pixels
            y, x = coord
            c = plt.Circle((x, y), r, color='red', linewidth=2, fill=False)
            ax[1].add_patch(c)


    fig.tight_layout()
    plt.show()
    return

def increase_contrast(im, method = 'adaptive'):
    """ Adative method seems to deal with background gradients the best, but two other options are possible using scikit package
    """
    ## SEE: https://scikit-image.org/docs/dev/auto_examples/color_exposure/plot_equalize.html
    from skimage import exposure

    if method == 'adaptive':
        img_hicontrast = exposure.equalize_adapthist(im, clip_limit=0.03)

    if method == 'contrast_stretching':
        p2, p98 = np.percentile(im, (2, 98))
        img_hicontrast = exposure.rescale_intensity(im, in_range=(p2, p98))

    if method == 'histogram_equalization':
        img_hicontrast = skimage.exposure.equalize_hist(im)

    return img_hicontrast

def find_local_peaks(im_array, im_array_filtered = None, particle_diameter_pixels = -1, min_peak_distance = -1, peak_threshold = 0.5, blurring_factor = 2, NEGATIVE_STAIN = False):
    from skimage.feature import peak_local_max
    from skimage.filters import gaussian
    from scipy import ndimage

    if blurring_factor < 0:
        ## prevent the blurring factor from being negative
        blurring_factor = 2

    if particle_diameter_pixels <= 0:
        ## if the particle diameter given is out of range, set it arbitrarily to 50 pixels
        particle_diameter_pixels = 50

    if min_peak_distance <= 0 :
        ## if minimum distance given is out of range, set it arbitrarily to 75% the particle diameter
        min_peak_distance = int(particle_diameter_pixels * 0.75)

    print("======================================================================")
    print(" Finding local peaks... ")
    print("-------------------------------------------------------")
    print("    particle_diameter_pixels = %s px" % particle_diameter_pixels)
    print("    peak_threshold = %s px" % peak_threshold)
    print("    min_peak_distance = %s px" % min_peak_distance)
    print("    blurring_factor = %s sigma" % blurring_factor)
    print("    negative stain mode = %s" % NEGATIVE_STAIN)

    ## set the background window arbitrarily as equal to half the particle size
    background_window_size = int(particle_diameter_pixels * 0.5)

    ## if a filtered image is provided, use that
    if im_array_filtered is not None:
        im = im_array_filtered
        print("    filtered image supplied for analysis" % NEGATIVE_STAIN)
    else:
        im = im_array

    ## blur the input image slightly
    filtered_im = gaussian(im, sigma = blurring_factor)

    ## if we have a negative stain image, we need to invert the image color space
    if NEGATIVE_STAIN == True:
        filtered_im = invert_image(filtered_im)

    # image_max is the dilation of im with a structuring element of given size
    image_max = ndimage.maximum_filter(filtered_im, size=background_window_size, mode='nearest')
    # using the max background, subtract the image to create an inverted signal (white = high signal, black = low)
    subtracted_im = image_max - filtered_im

    subtracted_im = increase_contrast(subtracted_im)

    # Comparison between image_max and im to find the coordinates of local maxima
    coordinates = peak_local_max(subtracted_im, min_distance = min_peak_distance, threshold_rel = peak_threshold)

    print("-------------------------------------------------------")
    print(" >> %s peaks found" % coordinates.shape[0])

    ## this script is not very efficient, so abort running if there are too many peaks and tell the user to adjust parameters and run again
    if coordinates.shape[0] > 1500:
        print(" !! Too many peaks, try increasing the Threshold value or Min. distance and run again")
        return

    ## although it shouldn't, the peak_local_max algorithm sometimes returns duplicate coordintes, clean the the coordinate dataset by removing these duplicates manually
    coordinates = remove_duplicates(coordinates, particle_diameter_pixels = particle_diameter_pixels)

    coordinates = remove_edge_coords(coordinates, particle_diameter_pixels, im_array.shape)

    return coordinates

def remove_edge_coords(data, particle_diameter_pixels, im_shape):
    """
    For an input numpy array of data points, remove points that are too close to the edge of the image.
    The cutoff is set arbitrarily as 0.75 the particle diameter
    The input array is typically derived from skimage pixel positions, which is of the form (row, column), e.g. (y, x) in conventional axes.
    The input array shape should be a [n, 2] matrix, where n = # of points in dataset, e.g.:
            [  [y1, x1]
               [y2, x2]
               ...
               [yn, xn] ]
    This function will return a new numpy array with the offending points removed (keeping the first instance of a clashing/duplicate point).
    """

    ## if minimum distance given is out of range, set it arbitrarily to 45 pixels (75% of 60 pixel diameter)
    edge_cutoff_threshold = int(particle_diameter_pixels * 0.75)

    # initialize the list variables for use in algorithm
    edge_points = []
    edge_points_removed = []
    ## convert the numpy arrays for each point into tuples of the form (x, y), which requires inverting the incoming tuple
    input_data =  list(map(tuple, np.flip(data, axis = 1)))

    for step in range(len(input_data)) :
        ## extract first entry in the list before removing it
        first_entry = input_data[0]
        x, y = first_entry
        # update the list of points to remove the current one to be worked on
        del input_data[0]
        # test if point is along any of the edges of the image
        if x < edge_cutoff_threshold or y < edge_cutoff_threshold :
            if first_entry not in edge_points:
                # print("Edge detected = (x, y) -> (%s, %s)" % (x, y))
                edge_points.append(first_entry)
        elif x > im_shape[1] - edge_cutoff_threshold or y > im_shape[0] - edge_cutoff_threshold :
            if first_entry not in edge_points:
                # print("Edge detected = (x, y) -> (%s, %s)" % (x, y))
                edge_points.append(first_entry)
        else:
            ## we can add this point to the output list
            edge_points_removed.append(first_entry)

    print("======================================================================")
    print(" Removing points too close to edge... ")
    print("-------------------------------------------------------")
    print("    image dimensions = (%s, %s)" % (im_shape[1], im_shape[0]))
    print("    particle_diameter_pixels = %s px" % particle_diameter_pixels)
    print("    edge_cutoff_threshold = %s px" % int(particle_diameter_pixels * 0.75))
    print("-------------------------------------------------------")
    print(" >> %s points removed, %s remaining " % ( len(edge_points), len(edge_points_removed)))

    ## convert the output coordinates back to a numpy array of arrays in the order of (row, column), e.g. (y, x)
    for i in range(len(edge_points_removed)-1):
        ## for the first point we initialize a new numpy array with the first entry
        if i == 0:
            output_data = np.array((edge_points_removed[i][1], edge_points_removed[i][0]))
        ## for subsequent points we stack onto the previously created array
        else :
            coord_array = np.array((edge_points_removed[i][1], edge_points_removed[i][0]))
            output_data = np.vstack((output_data, coord_array))

    return output_data

def remove_duplicates(data, min_distance = -1, particle_diameter_pixels = -1):
    """
    For an input numpy array of data points, remove duplicates or points that are within a clashing distance.
    The input array is typically derived from skimage pixel positions, which is of the form (row, column), e.g. (y, x) in conventional axes.
    The input array shape should be a [n, 2] matrix, where n = # of points in dataset, e.g.:
            [  [y1, x1]
               [y2, x2]
               ...
               [yn, xn] ]
    This function will return a new numpy array with the offending points removed (keeping the first instance of a clashing/duplicate point).
    """
    if min_distance <= 0 : ## in pixels
        ## if minimum distance given is out of range, set it arbitrarily to 45 pixels (75% of 60 pixel diameter)
        min_distance = int(particle_diameter_pixels * 0.6)

    # initialize the list variables for use in algorithm
    clashing_points = []
    duplicate_points = []
    duplicates_removed = list(map(tuple, np.flip(data, axis = 1)))
    ## convert the numpy arrays for each point into tuples of the form (x, y), which requires inverting the incoming tuple
    input_data =  list(map(tuple, np.flip(data, axis = 1)))

    for step in range(len(input_data)):
    	# extract first entry in the list
    	first_entry = input_data[0]
    	# update the list of points to remove the current one to be worked on
    	del input_data[0]
    	# test current point against all others in the dataset
    	for point in input_data:
    		# calculate the different vector for each pointwise comparison
    		diff_vector = np.subtract(first_entry[:2], point[:2])
    		# calculate the norm (length) of each difference vector
    		norm = np.linalg.norm(diff_vector)
    		# check if there are duplicates in the dataset
    		if norm <= 0 :
    			if first_entry not in duplicate_points:
    				duplicate_points.append(first_entry)
    		# add each point to the offending list if their norms are shorter than a given cutoff
    		if norm <= min_distance :
    			# add each point to the offending list only if it is not already present
    			if first_entry not in clashing_points:
    				clashing_points.append(first_entry)
    			if point not in clashing_points:
    				clashing_points.append(point)

    ## remove all points that are present in either duplicates or clashing points lists
    duplicates_removed = set(duplicates_removed) - set(clashing_points + duplicate_points)

    print("======================================================================")
    print(" Removing duplicate/clashing points... ")
    print("-------------------------------------------------------")
    print("    min_distance = %s px" % min_distance)
    print("    particle_diameter_pixels = %s px" % particle_diameter_pixels)
    print("-------------------------------------------------------")
    print(" >> %s points removed, %s remaining (%s duplicates, %s clashes)" % ( len(duplicate_points) + len(clashing_points), len(duplicates_removed), len(duplicate_points), len(clashing_points)))


    ## convert the output coordinates back to a numpy array of arrays in the order of (row, column), e.g. (y, x)
    i = 0
    for coord in duplicates_removed:
        ## for the first point we initialize a new numpy array with the first entry
        if i == 0:
            output_data = np.array((coord[1], coord[0]))
        else:
            coord_array = np.array((coord[1], coord[0]))
            output_data = np.vstack((output_data, coord_array))
        i += 1


    return output_data

def simplify_image(im_array, iterations = 3):
    ## pass the image through multiple rounds of dilation & erosion to segment the image
    im_cleaned = multi_ero(multi_dil(im_array, iterations), iterations)
    return im_cleaned

def multi_dil(im,num):
    from skimage import morphology
    for i in range(num):
        im = morphology.dilation(im)
    return im

def multi_ero(im,num):
    from skimage import morphology
    for i in range(num):
        im = morphology.erosion(im)
    return im

def circle_region(resolution, center, radius):
    """ For use with matplotlib to draw circles around a given point
            resolution = pixels used to draw circle
            center = coordinates as an array in the form: [y, x], e.g. row, column
            radius = size of the circle
        To use, plot all points, omitting the final point (which is a replicate of the first point), e.g.:
            points = circle_region(50, [y, x], particle_radius)[:-1]
    """
    radians = np.linspace(0, 2*np.pi, resolution)
    c = center[1] + radius*np.cos(radians)#polar co-ordinates
    r = center[0] + radius*np.sin(radians)
    return np.array([c, r]).T

def refine_coordinates(im_array, init_coords, im_array_filtered = None, search_box_size = -1, max_refinement_distance = -1, particle_radius = -1, blurring_factor = -1, refine_method = "thresholding", refinement_threshold = -1, display_results = False, NEGATIVE_STAIN = False):
    from matplotlib import pyplot as plt

    ## ensure the max refinement distance is within a logical range
    if max_refinement_distance <= 0 or max_refinement_distance > search_box_size:
        max_refinement_distance = int(particle_radius * 1.8)

    ## if input search local area size is not a legal value, just a size that is ~1.5 times larger than the particle size
    if search_box_size <= 0:
        search_box_size = particle_radius * 3

    ## set the refinement_threshold default and make sure the input value is within a logical range of [0, 1]
    if  0 > refinement_threshold > 1:
        refinement_threshold = 0.1

    print("======================================================================")
    print(" Refine peak positions by local %s ... " % refine_method)
    print("-------------------------------------------------------")
    print("    search_box_size = %s px" % search_box_size)
    print("    particle_radius = %s px" % particle_radius)
    print("    max_refinement_distance = %s px" % max_refinement_distance)
    print("    blurring_factor = %s sigma" % blurring_factor)
    print("    refinement_threshold = %s" % refinement_threshold)
    print("    negative stain mode = %s" % NEGATIVE_STAIN)

    ## prepare the data structure for output coordinates
    refined_coordinates = np.zeros(shape = init_coords.shape, dtype=np.int16)

    ## if a filtered image is provided, use that for processing
    if im_array_filtered is not None:
        im = im_array_filtered
        print("    specific filtered image supplied for analysis" % NEGATIVE_STAIN)
    else:
        im = im_array

    print("-------------------------------------------------------")

    ## prepare the figure to hold data as we draw if we choose to display results
    if display_results == True:
        fig, axes = plt.subplots(3, 3, sharex=True, sharey=True)
        ax = axes.ravel()

    ## iterate over each coordinate provided and carve out a region on the image for analysis by the chosen refinement method
    n = 0
    t = 0
    for coord in init_coords:
        n += 1
        print(" >> Refining peak #%s" % n, end='\r')
        y, x = coord[0], coord[1]

        ## edge detection, dont run refinement if point is too near an edge
        search_box_halfsize = int(search_box_size / 2)
        if x < search_box_halfsize or y < search_box_halfsize :
            refined_offset = [search_box_halfsize + 1 , search_box_halfsize + 1]
        elif x > im.shape[1] - search_box_halfsize or y > im.shape[0] - search_box_halfsize :
            refined_offset = [search_box_halfsize + 1 , search_box_halfsize + 1]
        else :
            local_region = im[y - search_box_halfsize : y + search_box_halfsize + 1, x - search_box_halfsize : x + search_box_halfsize + 1]
            if refine_method == "thresholding":
                refined_offset, origin_offset, input_img, blurred_img, bool_img = find_center_of_mass_via_thresholding(local_region, blur_sigma = blurring_factor, threshold = refinement_threshold, NEGATIVE_STAIN = NEGATIVE_STAIN)

                ## display 3 example cases of refined positions and what the algorithm is seeing
                if display_results == True and t < 9:
                    refined_points = circle_region(50, [refined_offset[1], refined_offset[0]], 2)
                    origin_points = circle_region(50, [origin_offset[1], origin_offset[0]], 2)
                    alpha_level = 0.6
                    line_width = 3

                    ax[t].imshow(input_img, cmap=plt.cm.gray)
                    ax[t].axis('off')
                    ax[t].set_title("Raw img")
                    ax[t].plot(refined_points[:, 0], refined_points[:, 1], 'r', lw = line_width, alpha = alpha_level)
                    ax[t].plot(origin_points[:, 0], origin_points[:, 1], 'b', lw = line_width, alpha = alpha_level)
                    ## draw a connected line to show the offset more clearly
                    ax[t].plot( [origin_offset[0], refined_offset[0]], [origin_offset[1], refined_offset[1]], linewidth = line_width, color='lime', alpha = alpha_level)
                    t += 1
                    ax[t].imshow(blurred_img, cmap=plt.cm.gray)
                    ax[t].axis('off')
                    ax[t].set_title("Blurred img")
                    t += 1
                    ax[t].imshow(bool_img, cmap=plt.cm.gray)
                    ax[t].axis('off')
                    ax[t].set_title("Bool img")
                    ax[t].plot(refined_points[:, 0], refined_points[:, 1], 'r', lw = line_width, alpha = alpha_level)
                    ax[t].plot(origin_points[:, 0], origin_points[:, 1], 'b', lw = line_width, alpha = alpha_level)
                    ax[t].plot( [origin_offset[0], refined_offset[0]], [origin_offset[1], refined_offset[1]], linewidth = line_width, color='lime', alpha = alpha_level)
                    t += 1

            elif refine_method == "contouring":
                refined_offset, origin_offset, input_img, blurred_img, bool_img, contours = find_center_of_mass_via_contouring(local_region, blur_sigma = blurring_factor, threshold = refinement_threshold, NEGATIVE_STAIN = NEGATIVE_STAIN)

                ## display 3 example cases of refined positions and what the algorithm is seeing
                if display_results == True and t < 9:
                    refined_points = circle_region(50, [refined_offset[1], refined_offset[0]], 2)
                    origin_points = circle_region(50, [origin_offset[1], origin_offset[0]], 2)
                    alpha_level = 0.6
                    line_width = 3

                    ax[t].imshow(input_img, cmap=plt.cm.gray)
                    ax[t].axis('off')
                    ax[t].set_title("Raw img")
                    ax[t].plot(refined_points[:, 0], refined_points[:, 1], 'r', lw = line_width, alpha = alpha_level)
                    ax[t].plot(origin_points[:, 0], origin_points[:, 1], 'b', lw = line_width, alpha = alpha_level)
                    ## draw a connected line to show the offset more clearly
                    ax[t].plot( [origin_offset[0], refined_offset[0]], [origin_offset[1], refined_offset[1]], linewidth = line_width, color='lime', alpha = alpha_level)
                    if len(contours) > 0:
                        for contour in contours:
                            ax[t].plot(contour[:, 1], contour[:, 0], linewidth = 3, alpha = 1)
                    t += 1
                    ax[t].imshow(blurred_img, cmap=plt.cm.gray)
                    ax[t].axis('off')
                    ax[t].set_title("Blurred img")
                    t += 1
                    ax[t].imshow(bool_img, cmap=plt.cm.gray)
                    ax[t].axis('off')
                    ax[t].set_title("Bool img")
                    ax[t].plot(refined_points[:, 0], refined_points[:, 1], 'r', lw = line_width, alpha = alpha_level)
                    ax[t].plot(origin_points[:, 0], origin_points[:, 1], 'b', lw = line_width, alpha = alpha_level)
                    ax[t].plot( [origin_offset[0], refined_offset[0]], [origin_offset[1], refined_offset[1]], linewidth = 4, color='lime', alpha = alpha_level)
                    if len(contours) > 0:
                        for contour in contours:
                            ax[t].plot(contour[:, 1], contour[:, 0], linewidth= 3, alpha = 1)
                    t += 1

            else:
                print(" ERROR :: Incorrect refine_method supplied -> %s " % refine_method)
                sys.exit()

            # print("Initial coordinate: %s -> refined position %s" % (coord, refined_position))

        if np.isnan(refined_offset[0]) or np.isnan(refined_offset[1]):
            refined_offset = [search_box_halfsize + 1 , search_box_halfsize + 1]
        refined_x = x - search_box_halfsize + refined_offset[1]
        refined_y = y - search_box_halfsize + refined_offset[0]
        ## update the coordinates for this point in the array we will output
        refined_coordinates[n - 1, 0] = refined_y
        refined_coordinates[n - 1, 1] = refined_x

    print(" >> %s peaks refined " % (n - 1))

    if display_results == True:
        fig.tight_layout()
        plt.show()

    refined_coordinates = remove_duplicates(refined_coordinates, particle_diameter_pixels = particle_radius * 2)
    refined_coordinates = remove_edge_coords(refined_coordinates, particle_radius * 2, im_array.shape)

    return refined_coordinates

def find_center_of_mass_via_contouring(im_array, threshold = 0.1, blur_sigma = -1, NEGATIVE_STAIN = False):
    """ A slower and more deliberate method for recentering peaks around continuous shapes. If the signal is strong enough, can be more accurate
        than thresholding as the center will be calculated for a non-circular shape (e.g. whatever the contouring algorithm finds), choosing the
        shape that is closest to the origin point.
    """

    ## keep threshold within a range of 0 and 1
    if threshold < 0 :
        threshold = 0
    elif threshold > 1 :
        threshold = 1
    ## avoid negative values for the blurring factor
    if blur_sigma < 0:
        blur_sigma = 0

    from skimage.filters import gaussian
    from skimage import measure
    from skimage.measure import label, regionprops
    import scipy.ndimage as ndimage

    ## blur the input image
    im = gaussian(im_array, sigma = blur_sigma)

    if NEGATIVE_STAIN:
        ## if negative stain, we do not need to invert the image
        pass
    else:
        ## invert the image so particle is white
        im = 1 - im

    ## contouring is more sensitive to non-intact signals (e.g. contours will form around smaller objects), hence image segmentation can help prevent this
    im = simplify_image(im,2)

    ## find the average intensity of the local area
    average_intensity = im.mean()
    ## find the indices of pixels above a threshold defined by the average intensity and a user adjustable threshold
    im_mask = im > average_intensity * (1 + threshold)
    ## initialize an empty black picture that matches the size of the local area
    bool_img = np.zeros(im.shape, dtype=np.uint8)
    ## paint the empty image with the pixels that passed the threshold limit above as white
    bool_img[im_mask] = 1

    ## find contours in the image
    contours = measure.find_contours(bool_img, level = 0.5, fully_connected = 'high')

    ## prepare variable to hold center of all contours
    all_contour_centroids = [] ## populate with tuples of the form: (x, y, sq_distance_to_origin)
    origin = (im.shape[1] / 2, im.shape[0] / 2) # (x, y)

    ## convert the boolean image into a labeled data structure
    label_img = label(bool_img)
    ## pass the labeled data structure into the regionprops function so we can extract its properties
    regions = regionprops(label_img)
    ## calculate a max distance limit for new coordinates
    max_sq_distance = ((origin[0] / 2)**2 + (origin[1] / 2)**2) * 0.5
    for props in regions:
        ## get the centroid of each region as a coordinate
        y, x = props.centroid
        ## round the centroid to the nearest pixel
        x, y = round(x), round(y)
        sq_distance = (x - origin[0])**2 + (y - origin[1])**2
        ## check if the distance is beyond a threshold
        if sq_distance > max_sq_distance :
            continue
        else:
            ## may want an edge intersection algorithm to drop contours that are not closed...
            all_contour_centroids.append((x,y, sq_distance))
            # print("centroid of contour = (%s, %s), sq. distance from origin = %s" %(x, y, sq_distance))
            # ax.plot(x, y, '.r', markersize=20)

    ## find the contour centroid closest to the origin and keep only that one
    if len(all_contour_centroids) > 0:
        min(all_contour_centroids, key = lambda t: t[2])
        center_of_mass_coordinate = min(all_contour_centroids, key = lambda t: t[2])[:2]
    else:
        center_of_mass_coordinate = origin

    return (center_of_mass_coordinate, origin, im_array, im, bool_img, contours) # refined coord, origin coord, input img, blurred img, bool img, contour coords

def find_center_of_mass_via_thresholding(im_array, threshold = 0.1, blur_sigma = -1, NEGATIVE_STAIN = False):
    """ Very fast and crude approach but can improve fit after local peak searching due to ability to handle unusual particle shapes.
        Uses a thresholding appraoch to find the local center of the input image. Pixels above the average pixel intensity + threshold value will be white and all below will be black.
        The center_of_mass function is then used to find the average location of signal in the given area.

        Returns the refined coordinate and images used in this algorithm for user feedback if desired.
    """
    from skimage.filters import gaussian
    import scipy.ndimage as ndimage

    ## keep threshold within a range of 0 and 1
    if threshold < 0 :
        threshold = 0
    elif threshold > 1 :
        threshold = 1
    ## avoid negative values for the blurring factor
    if blur_sigma < 0:
        blur_sigma = 0

    ## blur the input image
    im = gaussian(im_array, sigma = blur_sigma)

    if NEGATIVE_STAIN:
        ## if negative stain, we do not need to invert the image
        pass
    else:
        ## invert the image so particle is white
        im = 1 - im

    origin = (im.shape[1] / 2, im.shape[0] / 2) # (x, y)

    ## find the average intensity of the local area
    average_intensity = im.mean()
    ## find the indices of pixels above a threshold defined by the average intensity and a user adjustable threshold
    im_mask = im > average_intensity * (1 + threshold)
    ## initialize an empty black picture that matches the size of the local area
    bool_img = np.zeros(im.shape, dtype=np.uint8)
    ## paint the empty image with the pixels that passed the threshold limit above as white
    bool_img[im_mask] = 1

    ## find the center point of all white pixels
    center_of_mass_coordinate = ndimage.center_of_mass(bool_img)

    return ((center_of_mass_coordinate[1], center_of_mass_coordinate[0]), origin, im_array, im, bool_img)

def write_star_file(coordinates, gif_file, gif_pix_dimensions, mrc_pix_dimensions = (5760, 4092)):
    """ coordinates should be a numpy array of the form [ [y  x], ... ]
    """
    print(" Write coordinates into star file format ...")
    ## from the gif_file, get the base name of the micrograph
    gif_base_name = os.path.splitext(gif_file)[0]
    print("  >> Image data :: gif base name = %s, gif dimensions = (%s, %s), mrc dimensions = (%s, %s)" % (gif_base_name, gif_pix_dimensions[0], gif_pix_dimensions[1], mrc_pix_dimensions[0], mrc_pix_dimensions[1]))


    with open(gif_base_name + '_CURATED.star', 'w') as f : # NOTE: 'w' overwrites existing file; as compared to 'a' which appends only
        ############
        ## HEADER
        ############
        f.write("\n")
        f.write("data_\n")
        f.write("\n")
        f.write("loop_\n")
        f.write("_rlnCoordinateX #1\n")
        f.write("_rlnCoordinateY #2\n")
        f.write("_rlnClassNumber #3\n")
        f.write("_rlnAnglePsi #4\n")
        f.write("_rlnAutopickFigureOfMerit #5\n")
        f.write("\n")

        ############
        ## BODY
        ############
        for gif_coord in coordinates:
            #### interpolate .MRC coordinate from .GIF position
            mrc_x, mrc_y = gif2star((gif_coord[1], gif_coord[0]), gif_pix_dimensions, mrc_pix_dimensions)
            f.write("%.2f    %.2f   \t -999     -999.0    -999.0 \n" % (mrc_x, mrc_y))
    print("  ... written %s coordinates to file: %s" % (len(coordinates), gif_base_name + '_CURATED.star'))
    return

def gif2star(gif_coord, gif_dimensions, mrc_dimensions):
    """ Remap a coordinate in gif-space into star-space (e.g. rescale the image back to full size and invert the y-axis)
            gif_coord = tuple, (x, y)
            gif_dimensions = tuple, (x, y)
            mrc_dimensions = tuple, (x, y)
    """
    ## find the binning factor of the mrc image relative to the gif image we are working on
    scale_factor = mrc_dimensions[0] / gif_dimensions[0] # use the difference between the x-axis size to fine scale
    ## interpolate .MRC coordinate from .GIF position based on the scale factor
    rescaled_gif_coordinate_x = int(gif_coord[0] * scale_factor)
    rescaled_gif_coordinate_y = int(gif_coord[1] * scale_factor)

    ## invert y-axis to match RELION image coordinate convention
    inverted_rescaled_gif_coordinate_y = mrc_dimensions[1] - rescaled_gif_coordinate_y

    return (rescaled_gif_coordinate_x, inverted_rescaled_gif_coordinate_y)

def get_peaks(gif_file, particle_diameter_pixels, min_distance_pixels, threshold, blur = 2, NEGATIVE_STAIN = False, REFINE = True, refine_method = 'thresholding', refinement_threshold = -1, display_refinement_imgs = False, PRINT_STAR = False):
    """ Entry point function for external scripts to run analysis on a given image and
        returns a set of coordinates for use by the calling script in the form of:
            [(x1, y1), (x2, y2), ... (xn, yn)]
    """
    print()
    print(" ... RUNNING peak_finder.py")
    print("========================================================================================================")

    print(" Input parameters :: gif_file = %s, particle_diameter_pixels = %s, min_distance_pixels = %s, threshold = %s, blur = %s, NEGATIVE_STAIN = %s, REFINE = %s, refine_method = %s, refinement_threshold = %s,  display_refinement_imgs = %s, PRINT_STAR = %s" % (gif_file, particle_diameter_pixels, min_distance_pixels, threshold, blur, NEGATIVE_STAIN, REFINE, refine_method, refinement_threshold, display_refinement_imgs, PRINT_STAR))

    load_dependencies()

    ## read the image in as an array
    img = image_to_array(gif_file)

    ## use local contrasting to enhances features before picking
    img_filtered = increase_contrast(img)

    initial_coordinates = find_local_peaks(img_filtered, peak_threshold = threshold, particle_diameter_pixels = particle_diameter_pixels, min_peak_distance = min_distance_pixels, blurring_factor = blur, NEGATIVE_STAIN = NEGATIVE_STAIN) ## pick filtered image and display filtered image

    ## check if peak refinement is on
    if refine_method == "none":
        REFINE = False

    ## refine the position by searching a local area ...
    if REFINE == True:
        if refine_method == 'thresholding':
            refined_coordinates = refine_coordinates(img_filtered, initial_coordinates, search_box_size = -1, particle_radius = int(particle_diameter_pixels / 2), blurring_factor = blur,  refine_method = "thresholding", refinement_threshold = refinement_threshold, display_results = display_refinement_imgs, NEGATIVE_STAIN = NEGATIVE_STAIN)
        elif refine_method == 'contouring':
            refined_coordinates = refine_coordinates(img_filtered, initial_coordinates, search_box_size = -1, particle_radius = int(particle_diameter_pixels / 2), blurring_factor = blur,  refine_method = "contouring", refinement_threshold = refinement_threshold, display_results = display_refinement_imgs, NEGATIVE_STAIN = NEGATIVE_STAIN)
        else:
            print(" ERROR :: Incorrect refinement method keyword used -> (%s), try: 'thresholding' or 'contouring'" % refinement_method)

    ## print output files section
    if PRINT_STAR == True:
        if run_coordinate_refinement == True:
            write_star_file(refined_coordinates, input_file, (img.shape[1], img.shape[0]))
        else:
            write_star_file(initial_coordinates, input_file, (img.shape[1], img.shape[0]))

    print("========================================================================================================")
    print(" ... peak_finder.py COMPLETE")

    ## format the coordinates for use by the calling script
    output_coords = []
    if REFINE == True:
        if len(refined_coordinates) > 0:
            for (coord_y, coord_x) in refined_coordinates:
                output_coords.append((coord_x, coord_y))
    else:
        try:
            if len(initial_coordinates):
                for (coord_y, coord_x) in initial_coordinates:
                    output_coords.append((coord_x, coord_y))
        except:
            return output_coords
    return output_coords


####################################################
## RUN BLOCK
####################################################
if __name__ == '__main__':

    ################################################
    ## general I/O variables
    input_file = ''
    particle_diameter_pixels = 225
    min_distance_pixels = 200
    NEGATIVE_STAIN = False
    blurring_factor = 4
    ## local peaks variables
    local_peak_threshold = 0.2 # 0 to 1, reduce to get more peaks

    ## refinement variables
    run_coordinate_refinement = True
    refinement_method = 'contouring' ## options are: 'contouring' or 'thresholding'
    display_refinement_results = True ## will print out a display of the image and the initial and refined coordinates
    refinement_local_search_size = -1 # in pixels, box size of the local area to search for refined position >> NOT ASSIGNED YET NEED TO PASS IT INTO THE CENTER OF MASS FUNCTIONS THESE PARENT FUNCTIONS USE LATER!!
    refinement_threshold = -1 ## affects contour mapping, 0 to 1 >> NOT ASSIGNED YET NEED TO PASS IT INTO THE CENTER OF MASS FUNCTIONS THESE PARENT FUNCTIONS USE LATER!!
    refinement_blur_sigma = -1 ## affects contour mapping, 0 to inf >> NOT ASSIGNED YET NEED TO PASS IT INTO THE CENTER OF MASS FUNCTIONS THESE PARENT FUNCTIONS USE LATER!!
    refinement_debug = False ## if True, will display intermediate filtering images used during refinement steps

    ## output variables
    print_star_file = False

    ################################################

    print()
    print(" ... RUNNING peak_finder.py")
    print("========================================================================================================")

    ## load all packages necessary to run all functions with useful error handling
    load_dependencies()

    ## check proper usage and read in variables if correct
    read_input()

    ## read the image in as an array
    img = image_to_array(input_file)

    ## use local contrasting to enhances features before picking
    img_filtered = increase_contrast(img)

    ## Find particles using a local peak search algorithm
    # initial_coordinates = find_local_peaks(img, particle_diameter_pixels = particle_diameter_pixels, min_distance_pixels = min_distance_pixels, NEGATIVE_STAIN = NEGATIVE_STAIN) ## pick unfiltered image
    # initial_coordinates = find_local_peaks(img, im_array_filtered = img_filtered, particle_diameter_pixels = particle_diameter_pixels, min_distance_pixels = min_distance_pixels, NEGATIVE_STAIN = NEGATIVE_STAIN) ## pick filtered image but display unfiltered image
    initial_coordinates = find_local_peaks(img_filtered, peak_threshold = local_peak_threshold, particle_diameter_pixels = particle_diameter_pixels, min_peak_distance = min_distance_pixels, NEGATIVE_STAIN = NEGATIVE_STAIN) ## pick filtered image and display filtered image

    if run_coordinate_refinement:
        ## refine the position by searching a local area ...
        if refinement_method in ['thresholding', 'contouring']:
            refined_coordinates = refine_coordinates(img_filtered, initial_coordinates, search_box_size = int(particle_diameter_pixels * 1.5), particle_radius = int(particle_diameter_pixels / 2), blurring_factor = blurring_factor, refine_method = refinement_method, display_results = display_refinement_results, NEGATIVE_STAIN = NEGATIVE_STAIN)
        elif refinement_method == 'none':
            pass
        else:
            print("Incorrect refinement method option used (%s), try: 'thresholding' or 'contouring'" % refinement_method)


    ## file output section
    if print_star_file == True:
        if run_coordinate_refinement == True:
            write_star_file(refined_coordinates, input_file, (img.shape[1], img.shape[0]))
        else:
            write_star_file(initial_coordinates, input_file, (img.shape[1], img.shape[0]))

    print("========================================================================================================")
    print(" ... COMPLETE")
