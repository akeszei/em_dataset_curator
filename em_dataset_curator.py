#!/usr/bin/env python3

class MainUI:
    def __init__(self, master):
        self.master = master
        master.title("EM dataset curator")

        ####################################
        ## Menu bar layout
        ####################################
        ## initialize the top menu bar
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        ## add items to the menu bar
        dropdown_file = tk.Menu(menubar)
        menubar.add_cascade(label="File", menu=dropdown_file)
        dropdown_file.add_command(label="Open image", command=self.load_file)
        dropdown_file.add_command(label="Load marked filelist", command=self.load_marked_filelist)
        # dropdown_file.add_command(label="Import .box coordinates", command=self.load_boxfile_coords)
        dropdown_file.add_command(label="Print marked imgs (Ctrl+S)", command=self.write_marked)
        dropdown_file.add_command(label="Exit", command=self.quit)

        dropdown_functions = tk.Menu(menubar)
        menubar.add_cascade(label="Functions", menu=dropdown_functions)
        dropdown_functions.add_command(label="Local contrast", command=self.local_contrast)
        dropdown_functions.add_command(label="Blur", command=self.gaussian_blur)
        dropdown_functions.add_command(label="Auto-contrast", command=self.auto_contrast)
        dropdown_functions.add_command(label="Contrast from selection", command=self.contrast_by_selected_particles)
        dropdown_functions.add_command(label="Reset img", command=self.load_img)

        dropdown_autopick = tk.Menu(menubar)
        menubar.add_cascade(label="Autopicking", menu=dropdown_autopick)
        dropdown_autopick.add_command(label="Make bool img", command = lambda: self.open_panel("BoolImgPanel"))
        dropdown_autopick.add_command(label="Autopick", command = lambda: self.open_panel("AutopickPanel"))
        dropdown_autopick.add_command(label="Clear coordinates", command=self.clear_coordinates)

        dropdown_resize = tk.Menu(menubar)
        menubar.add_cascade(label="Resize img", menu=dropdown_resize)
        dropdown_resize.add_command(label="Original", command= lambda: self.toggle_img_resize(100))
        dropdown_resize.add_command(label="75%", command= lambda: self.toggle_img_resize(75))
        dropdown_resize.add_command(label="50%", command= lambda: self.toggle_img_resize(50))
        dropdown_resize.add_command(label="25%", command= lambda: self.toggle_img_resize(25))

        dropdown_help = tk.Menu(menubar)
        menubar.add_cascade(label="Help", menu=dropdown_help)
        dropdown_help.add_command(label="How to use", command = lambda: self.open_panel("HelpPanel"))
        ####################################

        ####################################
        ## Widget setup/functions
        ####################################
        self.canvas = tk.Canvas(master, width = 650, height = 600, background="gray", cursor="cross red red")
        # self.current_dir = Label(master, font=("Helvetica", 12), text="")
        self.input_text = tk.Entry(master, width=30, font=("Helvetica", 16), highlightcolor="blue", borderwidth=None, relief=tk.FLAT, foreground="black", background="light gray")
        # self.browse = Button(master, text="Browse", command=self.load_file, width=10)
        self.settings_header = tk.Label(master, font=("Helvetica, 16"), text="Settings")
        self.mrc_dimensions_label = tk.Label(master, font=("Helvetica", 12), text=".MRC dimensions (X, Y)")
        self.input_mrc_dimensions = tk.Entry(master, width=18, font=("Helvetica", 12))
        self.input_mrc_dimensions.insert(tk.END, "%s, %s" % (PARAMS['mrc_dimensions'][0], PARAMS['mrc_dimensions'][1]))
        self.mrc_box_size_label = tk.Label(master, font=("Helvetica, 12"), text="Box size (Ang)")
        self.input_mrc_box_size = tk.Entry(master, width=18, font=("Helvetica", 12))
        self.input_mrc_box_size.insert(tk.END, "%s" % PARAMS['box_size'])
        self.angpix_label = tk.Label(master, font=("Helvetica", 12), text=".MRC Ang/pix")
        self.input_angpix = tk.Entry(master, width=18, font=("Helvetica", 12))
        self.input_angpix.insert(tk.END, "%s" % PARAMS['angpix'])
        self.NEGATIVE_STAIN = tk.BooleanVar(master, False)
        self.negative_stain_toggle = tk.Checkbutton(master, text='Negative stain', variable=self.NEGATIVE_STAIN, onvalue=True, offvalue=False, command=self.toggle_negative_stain)
        self.separator = ttk.Separator(master, orient='horizontal')
        self.autopick_header = tk.Label(master, font=("Helvetica, 16"), text="Autopicking")
        self.autopick_button = tk.Button(master, text="Autopick", command=self.default_autopick, width=10)
        ####################################

        ####################################
        ## Widget layout
        ####################################
        self.input_text.grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)
        self.canvas.grid(row=1, column=0, rowspan=100) #rowspan=0)

        self.settings_header.grid(row=1, column = 1, sticky = tk.W)
        self.mrc_dimensions_label.grid(row=4, column=1, padx=5, sticky=(tk.S, tk.W))
        self.input_mrc_dimensions.grid(row=5, column=1, padx=5, pady=0, sticky=(tk.N, tk.W))
        self.mrc_box_size_label.grid(row=6, column=1, padx=5, pady=0, sticky=(tk.S, tk.W))
        self.input_mrc_box_size.grid(row=7, column=1, padx=5, pady=0, sticky=(tk.N, tk.W))
        self.angpix_label.grid(row=9, column=1, padx=5, pady=0, sticky=(tk.S, tk.W))
        self.input_angpix.grid(row=10, column=1, padx=5, pady=0, sticky=(tk.N, tk.W))

        self.separator.grid(row=20, column =1, sticky=tk.EW)
        self.autopick_header.grid(row=21, column = 1, sticky = tk.W)
        self.negative_stain_toggle.grid(row=22, column=1, padx=5, pady=0, sticky=tk.N)
        self.autopick_button.grid(row=25, column=1, padx =5, pady=0, sticky=tk.N)
        ####################################
        ####################################
        ## Keybindings
        ####################################
        self.canvas.bind('<Left>', lambda event: self.next_img('left'))
        self.canvas.bind('<Right>', lambda event: self.next_img('right'))
        self.canvas.bind('<z>', lambda event: self.next_img('left'))
        self.canvas.bind('<x>', lambda event: self.next_img('right'))
        self.canvas.bind('<d>', lambda event: self.mark_img())
        # self.canvas.bind('<F1>', lambda event: self.debug())
        self.canvas.bind('<Escape>', lambda event: self.quit())
        self.input_text.bind('<Control-KeyRelease-a>', lambda event: self.select_all(self.input_text))
        self.input_text.bind('<Return>', lambda event: self.choose_img())
        self.input_text.bind('<KP_Enter>', lambda event: self.choose_img()) # numpad 'Return' key
        self.input_mrc_dimensions.bind('<Return>', lambda event: self.new_mrc_dimensions())
        self.input_mrc_dimensions.bind('<KP_Enter>', lambda event: self.new_mrc_dimensions()) # numpad 'Return' key
        self.input_angpix.bind('<KP_Enter>', lambda event: self.new_angpix()) # numpad 'Return' key
        self.input_angpix.bind('<Return>', lambda event: self.new_angpix())
        self.input_mrc_box_size.bind('<Return>', lambda event: self.new_box_size())
        self.input_mrc_box_size.bind('<KP_Enter>', lambda event: self.new_box_size()) # numpad 'Return' key
        self.autopick_button.bind('<Return>', lambda event: self.default_autopick())
        self.autopick_button.bind('<KP_Enter>', lambda event: self.default_autopick())

        self.canvas.bind('<Control-KeyRelease-s>', lambda event: self.write_marked())
        self.canvas.bind("<ButtonPress-1>", self.on_left_mouse_down)
        self.canvas.bind("<ButtonPress-2>", self.on_middle_mouse_press)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_mouse_release)
        self.canvas.bind("<ButtonPress-3>", self.on_right_mouse_press)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_mouse_release)
        self.canvas.bind("<Motion>", self.delete_brush_cursor)
        self.canvas.bind("<MouseWheel>", self.MouseWheelHandler) # Windows, Mac: Binding to <MouseWheel> is being used
        self.canvas.bind("<Button-4>", self.MouseWheelHandler) # Linux: Binding to <Button-4> and <Button-5> is being used
        self.canvas.bind("<Button-5>", self.MouseWheelHandler)
        self.canvas.bind("<F1>", lambda event: self.print_parameters())
        ####################################

        self.master.protocol("WM_DELETE_WINDOW", self.quit)
        ## Run function to check for settings files and, if present load them into variables
        self.load_settings()
        ## Set focus to canvas, which has arrow key bindings
        self.canvas.focus_set()

        ####################################
        ## Panel Instances
        ####################################
        self.boolImgPanel_instance = None
        self.autopickPanel_instance = None
        self.helpPanel_instance = None
        ####################################

    def open_panel(self, panelType = 'None'):
        global PARAMS
        current_im_data = PARAMS['current_img_data']

        ## use a switch-case statement logic to open the correct panel
        if panelType == "None":
            return
        elif panelType == "BoolImgPanel":
            ## create new instance if none exists
            if self.boolImgPanel_instance is None:
                self.boolImgPanel_instance = BoolImgPanel(self, current_im_data)
            ## otherwise, do not create an instance
            else:
                print(" BoolImgPanel is already open: ", self.boolImgPanel_instance)
        elif panelType == "AutopickPanel":
            if self.autopickPanel_instance is None:
                self.autopickPanel = AutopickPanel(self)
            else:
                print(" AutopickPanel is already open: ", self.autopickPanel_instance)
        elif panelType == "HelpPanel":
            if self.helpPanel_instance is None:
                self.helpPanel = HelpPanel(self)
            else:
                print(" HelpPanel is already open: ", self.helpPanel_instance)
        else:
            return
        return

    def get_resized_dimensions(self, percent, input_dimensions):
        """
        PARAMETERS:
            percent = % size to change from original (i.e. 50 would shrink by half)
            input_dimensions = tuple(x, y); pixel size of original image
        RETURNS:
            new_dimensions = tuple(x, y); the dimensions of the image after applying the percent scaling
        """
        new_dimension_x = int(input_dimensions[0] * (percent / 100))
        new_dimension_y = int(input_dimensions[1] * (percent / 100))
        new_dimensions = (new_dimension_x, new_dimension_y)
        return new_dimensions

    def toggle_img_resize(self, percent):
        """ Switch to set global values for resizing the image on load.
        PARAMETERS
            percent = int(), where value is given from 1 to 100
        RETURNS
            None, sets global dictionary parameters and forces an image redraw
        """
        global PARAMS
        print(" Resize image by %s" % percent, "%")
        ## turn on resize toggle
        PARAMS['RESIZE_IMG'] = True
        ## set the value
        PARAMS['img_resize_percent'] = percent
        ## call an image reload
        self.load_img()
        return

    def print_parameters(self):
        """ Tied to a hotkey (F1) to print out current dictionary parameters for debugging
        """
        global PARAMS
        print("=========================================================================")
        print("  EM DATASET CURATOR PARAMETERS:")
        print("-------------------------------------------------------------------------")
        for param in PARAMS:
            if param == 'img_coords':
                print("  %s : %s coordinates" % ("{:<20}".format(param[:20]), len(PARAMS[param])))
            elif param == 'img_list':
                print("  %s : %s imgs" % ("{:<20}".format(param[:20]), len(PARAMS[param])))
            elif param == 'marked_imgs':
                print("  %s : %s marked imgs" % ("{:<20}".format(param[:20]), len(PARAMS[param])))
            elif param == 'original_img_data' or param == 'current_img_data':
                print("  %s :" % ("{:<20}".format(param[:20])), PARAMS[param].shape, "pixels")
            else:
                print("  %s : %s" % ("{:<20}".format(param[:20]), PARAMS[param]))
        print("=========================================================================")

        return

    def quit(self):
        self.save_settings()
        print("==============================================")
        print(" CLOSING PROGRAM")
        print("==============================================")
        print()
        print(" Convert curated star files into manualpick file names with the following bash command:")
        print()
        print('         for fname in *.star; do mv -v $fname ${fname/_CURATED.star/}_manualpick.star; done')
        print()
        ## close the program
        sys.exit()

    def get_scale_factor(self, mrc_dimensions, img_dimensions):
        """ For a given set of image & mrc dimensions, determine the scaling factor between them, (i.e. how
            much smaller the image is relative to the original mrc file.
        PARAMETERS
            mrc_dimensions = tuple(x, y), in pixels
            img_dimensions = tuple(x, y), in pixels
        RETURNS
            scaling_factor = float(), how much smaller the img is to the mrc
        """
        x_scaling_factor = mrc_dimensions[0] / img_dimensions[0]
        y_scaling_factor = mrc_dimensions[1] / img_dimensions[1]
        if round(x_scaling_factor, 2) != round(y_scaling_factor, 2):
            print(" WARNING :: Image is not proportionally smaller than .MRC!")

        scaling_factor = (x_scaling_factor + y_scaling_factor) / 2
        return scaling_factor

    def gif2star(self, gif_coord, scaling_factor):
        """ Remap a coordinate in image-space (.gif, .jpg, .png, etc...) into star-space (e.g. .mrc)
        PARAMETERS
            gif_coord = tuple(x, y)
        RETURNS
            star_coord = tuple(x, y)
        """
        ### interpolate .MRC coordinate from .GIF position based on the scale factor
        rescaled_gif_coordinate_x = int(gif_coord[0] * scaling_factor)
        rescaled_gif_coordinate_y = int(gif_coord[1] * scaling_factor)

        ### invert y-axis to match RELION image coordinate convention
        ## 2021-09-10: WRONG implementation, RELION v.3.1 no longer inverts y-axis on .STAR data?
        # inverted_rescaled_gif_coordinate_y = mrc_pixel_size_y - rescaled_gif_coordinate_y
        inverted_rescaled_gif_coordinate_y = rescaled_gif_coordinate_y

        return (rescaled_gif_coordinate_x, inverted_rescaled_gif_coordinate_y)

    def star2gif(self, star_coord, scaling_factor):
        """ Remap a coordinate in star-space into gif-space
        PARAMETERS:
            star_coord = tuple(x, y); in pixels
            scaling_factor = float(); size difference between reference image and original .MRC file
        RETURNS:
            gif_coord = tuple, (x, y)
        """
        star_coord = ( star_coord[0], star_coord[1] )

        ### interpolate from .MRC to .GIF coordinates based on the scale factor
        rescaled_star_coordinate_x = int(star_coord[0] / scaling_factor)
        rescaled_star_coordinate_y = int(star_coord[1] / scaling_factor)

        return (rescaled_star_coordinate_x, rescaled_star_coordinate_y)

    def read_coords_from_star(self, starfile):
        """ Read an input star file and retrieve the x and y coordinates, remapping them onto the display image. To avoid
            degradation of original input coordinates due to the transformation/remapping step, coordinates are saved into
            a global dictionary, where original points are tied to the remapped point and are not updated, except when erased.
        PARAMETERS:
            starfile = string(file name to load)
        RETURNS:
            image_coordinates = {   (gif_x1, gif_y1) : (star_x1, star_y1),
                                    (gif_x2, gif_y2) : (star_x2, star_y2),
                                    ...,
                                    (gif_xn, gif_yn) : (star_xn, star_yn) }
        """
        global PARAMS

        image_coordinates = dict()

        header_size = self.header_length(starfile)
        star_X_coord_column = self.find_star_column(starfile, "_rlnCoordinateX", header_size)
        star_Y_coord_column = self.find_star_column(starfile, "_rlnCoordinateY", header_size)

        with open(starfile, 'r') as f:
            counter = 0
            line_num = 0
            for line in f:
                line_num += 1
                ## avoid reading into the header
                if (line_num <= header_size): continue

                star_X_coord = self.find_star_info(line, star_X_coord_column)
                star_Y_coord = self.find_star_info(line, star_Y_coord_column)

                ## avoid empty lines by checking if the X and Y coordinates exist
                if not star_X_coord:
                    continue
                if not star_Y_coord:
                    continue

                counter += 1
                star_coord = (int(float(star_X_coord)), int(float(star_Y_coord)))
                img_coord = self.star2gif(star_coord, self.get_scale_factor(PARAMS['mrc_dimensions'], PARAMS['img_dimensions']))

                image_coordinates[ img_coord ] = star_coord # data are linked in this way to avoid transformation data loss

            print(">> %s particles read from star file %s" % (counter, starfile) )
        ## update global dictionary after parsing is complete
        PARAMS['img_coords'] = image_coordinates
        return

    def update_input_widgets(self):
        """ Updates the input widgets on the main GUI to take on the values of the global dictionary.
            Mainly used after loading a new settings file.
        """
        global PARAMS
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        mrc_pixel_size_y = PARAMS['mrc_dimensions'][1]
        box_size = PARAMS['box_size']
        angpix = PARAMS['angpix']


        self.input_mrc_dimensions.delete(0, tk.END)
        self.input_mrc_dimensions.insert(0, "%s, %s" % (mrc_pixel_size_x, mrc_pixel_size_y) )

        self.input_mrc_box_size.delete(0, tk.END)
        self.input_mrc_box_size.insert(0, box_size)

        self.input_angpix.delete(0, tk.END)
        self.input_angpix.insert(0, angpix)

        return

    def save_settings(self):
        """ Write out a settings file for ease of use on re-launching the program in the same directory
        """
        global PARAMS, brush_size, current_im_data
        image_list = PARAMS['img_list']
        n = PARAMS['index']
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        mrc_pixel_size_y = PARAMS['mrc_dimensions'][1]
        angpix = PARAMS['angpix']
        box_size= PARAMS['box_size']

        save_fname = '.em_dataset_curator.config'
        ## sanity check a file is loaded into buffer, otherwise no reason to save settings
        try:
            current_im_data.any()
        except:
            print("Abort autopick :: Image not loaded")
            return

        current_img = image_list[n] # os.path.splitext(image_list[n])[0]
        ## save a settings file only if a project is actively open, as assessed by image_list being populated
        if len(image_list) > 0:
            with open(save_fname, 'w') as f :
                f.write("## Last used settings for em_dataset_curator.py\n")
                f.write("mrc_pixel_size_x %s\n" % mrc_pixel_size_x)
                f.write("mrc_pixel_size_y %s\n" % mrc_pixel_size_y)
                f.write("angpix %s\n" % angpix)
                f.write("brush_size %s\n" % brush_size)
                f.write("img_on_save %s\n" % current_img)
                f.write("box_size %s\n" % box_size)
            print(" >> Saved current settings to '%s'" % save_fname)

    def load_settings(self):
        """ On loadup, search the directory for input files and load them into memory automatically
                >> marked_imgs.txt :: load these filenames into the 'marked_imgs' list variable
        """
        global PARAMS, brush_size
        print("============================")
        print(" load_settings ")
        print("----------------------------")
        ## reset marked_imgs global variable
        marked_imgs = []
        ## repopulate the global marked_imgs variable based on the file 'marked_imgs.txt', if present
        if os.path.exists('marked_imgs.txt'):
            ## update marked file list with file in directory
            with open('marked_imgs.txt', 'r') as f :
                for line in f:
                    if not line.strip() in marked_imgs:
                        marked_imgs.append(line.strip())
        PARAMS['marked_imgs'] = marked_imgs

        settingsfile = '.em_dataset_curator.config'

        if os.path.exists(settingsfile):
            ## update marked file list with file in directory
            with open(settingsfile, 'r') as f :
                for line in f:
                    line2list = line.split()
                    if not '#' in line2list[0]: ## ignore comment lines
                        if line2list[0] == 'mrc_pixel_size_x':
                            mrc_pixel_size_x = int(line2list[1])
                            # PARAMS['mrc_pixel_size_x'] = int(line2list[1])
                        elif line2list[0] == 'mrc_pixel_size_y':
                            mrc_pixel_size_y = int(line2list[1])
                            # PARAMS['mrc_pixel_size_y'] = int(line2list[1])
                        elif line2list[0] == 'angpix':
                            PARAMS['angpix'] = float(line2list[1])
                        elif line2list[0] == 'brush_size':
                            brush_size = int(line2list[1])
                        elif line2list[0] == 'img_on_save':
                            PARAMS['img_on_save'] = line2list[1]
                        elif line2list[0] == 'box_size':
                            PARAMS['box_size'] = int(line2list[1])
                            print("  box_size = %s" % PARAMS['box_size'])

            ## set the dimensions
            PARAMS['mrc_dimensions'] = (mrc_pixel_size_x, mrc_pixel_size_y)
            ## update the widgets with the loaded values
            self.input_mrc_box_size.delete(0, tk.END)
            self.input_mrc_box_size.insert(0, PARAMS['box_size'])
            self.input_angpix.delete(0, tk.END)
            self.input_angpix.insert(0, PARAMS['angpix'])
            self.input_mrc_dimensions.delete(0, tk.END)
            self.input_mrc_dimensions.insert(0, "%s, %s" % (PARAMS['mrc_dimensions'][0], PARAMS['mrc_dimensions'][1]))

            # extract file information from selection
            file_name = PARAMS['img_on_save']
            print("File selected: "+ file_name)

            # erase any previous image list and repopulate it with the new directory
            image_list = []
            image_list = self.images_in_dir('.')
            PARAMS['img_list'] = image_list

            # find the index of the selected image in the new list
            try:
                PARAMS['index'] = image_list.index(file_name)
            except:
                print(" ERROR: Settings file points to image that does not exist in working directory! Resetting index to 0")

            ## redraw canvas items with updated global values as the given image index
            self.load_img()

        return

    def new_box_size(self):
        global PARAMS
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        mrc_pixel_size_y = PARAMS['mrc_dimensions'][1]
        img_pixel_size_x = PARAMS['img_dimensions'][0]
        angpix = PARAMS['angpix']

        user_input = self.input_mrc_box_size.get().strip()
        temp = re.findall(r'\d+', user_input)
        res = list(map(int, temp))

        ## kill function if no entry is given or if value is not even
        if not len(res) == 1 or not isinstance(res[0], int) or not res[0] > 0:
            self.input_mrc_box_size.delete(0, tk.END)
            self.input_mrc_box_size.insert(0, "ang boxsize")
            return
        elif not (res[0] % 2 == 0): # check if value is even
            self.input_mrc_box_size.delete(0, tk.END)
            self.input_mrc_box_size.insert(0, "value must be even")
            return
        ## set the global box_size to the input field value
        box_size = res[0]

        ## update the global dictionary
        PARAMS['box_size'] = box_size
        ## calculate the image box size in pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        img_angpix = angpix * scale_factor
        img_box_size = int(box_size / img_angpix)
        PARAMS['img_box_size'] = img_box_size
        ## redraw boxes by first deleting it then redrawing it
        self.draw_image_coordinates()
        ## revert focus to main canvas
        self.canvas.focus_set()
        return

    def new_mrc_dimensions(self):
        """ Update the global variables for mrc_dimensions from user input in the main window.
            Call a redraw of the image & boxes after.
        """
        global PARAMS
        n = PARAMS['index']
        image_list = PARAMS['img_list']
        file_dir = PARAMS['file_dir']

        user_input = self.input_mrc_dimensions.get().strip()
        temp = re.findall(r'\d+', user_input)
        res = list(map(int, temp))

        if not len(res) == 2:
            self.input_mrc_dimensions.delete(0, tk.END)
            self.input_mrc_dimensions.insert(0, "mrc_X, mrc_Y")
            return
        else:
            mrc_pixel_size_x = res[0]
            mrc_pixel_size_y = res[1]
            PARAMS['mrc_dimensions'] = (mrc_pixel_size_x, mrc_pixel_size_y)

            ## check for an associated .star file with input coordinates to read
            counter = 0
            star_coordinate_file = ""
            ## find the matching star file if it exists
            for fname in os.listdir(file_dir): ## iterate over the directory
                base_image_name = os.path.splitext(image_list[n])[0] ## get the base name of the .GIF file
                counter = 0
                star_coordinate_file = ""
                if base_image_name in fname and fname[-5:] == ".star": ## find any files that match the base .GIF file name and end in .STAR
                    counter += 1
                    star_coordinate_file = fname
                    if counter > 1: print(">>> WARNING: Multiple .STAR files found for this image (e.g. multiple files match: " + base_image_name + "*.star)")
                    ## This program writes out ..._CURATED.star files, if we find one - use that over all other available .STAR files
                    if star_coordinate_file[-13:] == "_CURATED.star": break
            ## if a star file is found, load its coordinates
            # print(" STAR FILE USED FOR COORDS = ", star_coordinate_file)
            if (star_coordinate_file != ""):
                self.read_coords_from_star(star_coordinate_file)

            ## redraw particle positions and boxsize with the new remapped data
            self.draw_image_coordinates()
        ## revert focus to main canvas
        self.canvas.focus_set()
        return

    def new_angpix(self):
        """ Update the global 'angpix' variable from user input in the main window
        """
        global PARAMS
        user_input = self.input_angpix.get().strip()
        try:
            res = float(user_input)
            angpix = res
            PARAMS['angpix'] = angpix
            ## we need to recalculate the label for box size in angstroms
            # self.box_size_ang.config(text="%s Angstroms" % (box_size * angpix))

        except:
            self.input_angpix.delete(0, tk.END)
            self.input_angpix.insert(0, "angpix")

        ## redraw the picked coordinates
        self.draw_image_coordinates()

        ## revert focus to main canvas
        self.canvas.focus_set()

    def MouseWheelHandler(self, event):
        """ See: https://stackoverflow.com/questions/17355902/python-tkinter-binding-mousewheel-to-scrollbar
            Tie the mousewheel to the brush size, draw a green square to show the user the final setting
        """
        global brush_size, PARAMS

        def delta(event):
            if event.num == 5 or event.delta < 0:
                return -2
            return 2

        brush_size += delta(event)

        ## avoid negative brush_size values
        if brush_size <= 0:
            brush_size = 0

        ## draw new brush size
        x, y = event.x, event.y
        x_max = int(x + brush_size/2)
        x_min = int(x - brush_size/2)
        y_max = int(y + brush_size/2)
        y_min = int(y - brush_size/2)
        brush = self.canvas.create_rectangle(x_max, y_max, x_min, y_min, outline="green2", tags='brush')

    def check_if_two_ranges_intersect(self, x0, x1, y0, y1):
        """ For two well-ordered ranges (x0 < x1; y0 < 1), check if there is any intersection between them.
            See: https://stackoverflow.com/questions/3269434/whats-the-most-efficient-way-to-test-two-integer-ranges-for-overlap/25369187
            An efficient way to quickly calculate if the erase brush hits a marked coordinate in the image.
        """
        ## sanity check input
        if (x0 > x1):
            print("ERROR: Incorrect range provided, x0 -> x1 == %s -> %s" % (x0, x1))

        if y0 > y1:
            print("ERROR: Incorrect range provided, y0 -> y1 == %s -> %s" % (y0, y1))

        if x0 <= y1 and y0 <= x1:
            return True
        else:
            return False

    def delete_brush_cursor(self, event):
        """ This function is tied to the <Motion> event.
            It constantly checks if the condition RIGHT_MOUSE_PRESSED is True, in which case it runs the erase-coordinates algorithm
        """
        global RIGHT_MOUSE_PRESSED, brush_size, PARAMS
        image_coordinates = PARAMS['img_coords']
        box_size = PARAMS['box_size']
        n = PARAMS['index']
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        mrc_pixel_size_y = PARAMS['mrc_dimensions'][1]
        img_pixel_size_x = PARAMS['img_dimensions'][0]

        if RIGHT_MOUSE_PRESSED:
            x, y = event.x, event.y

            self.canvas.delete('brush')

            x_max = int(x + brush_size/2)
            x_min = int(x - brush_size/2)
            y_max = int(y + brush_size/2)
            y_min = int(y - brush_size/2)

            brush = self.canvas.create_rectangle(x_max, y_max, x_min, y_min, outline="green2", tags='brush')

            ## box_size is a value given in Angstroms, we need to convert it to pixels
            scale_factor = self.get_scale_factor(PARAMS['mrc_dimensions'], PARAMS['img_dimensions']) # mrc_pixel_size_x / img_pixel_size_x
            angpix_gif = PARAMS['angpix'] * scale_factor
            gif_half_box_size = int((box_size / angpix_gif)/2) ## since coordinates are given as center, we need to add half the box size to each size of the coordinate

            erase_coordinates = [] # avoid changing dictionary until after iteration complete
            ## find all coordinates that clash with the brush
            if len(image_coordinates) > 0:
                for coord in image_coordinates:
                    if self.check_if_two_ranges_intersect(coord[0] - gif_half_box_size, coord[0] + gif_half_box_size, x_min, x_max): # x0, x1, y0, y1
                        if self.check_if_two_ranges_intersect(coord[1] - gif_half_box_size, coord[1] + gif_half_box_size, y_min, y_max): # x0, x1, y0, y1
                            erase_coordinates.append(coord)
            ## erase all coordinates caught by the brush
            for coord in erase_coordinates:
                del image_coordinates[coord] # remove the coordinate that clashed

            ## update global
            PARAMS['img_coords'] = image_coordinates

            self.draw_image_coordinates()
        else:
            return

    def on_right_mouse_press(self, event):
        global RIGHT_MOUSE_PRESSED, brush_size, PARAMS
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        mrc_pixel_size_y = PARAMS['mrc_dimensions'][1]
        angpix = PARAMS['angpix']
        box_size = PARAMS['box_size']
        image_coordinates = PARAMS['img_coords']
        img_pixel_size_x = PARAMS['img_dimensions'][0]

        RIGHT_MOUSE_PRESSED = True
        x, y = event.x, event.y
        search_size = int(brush_size/2)
        x_max = int(x + search_size)
        x_min = int(x - search_size)
        y_max = int(y + search_size)
        y_min = int(y - search_size)
        brush = self.canvas.create_rectangle(x_max, y_max, x_min, y_min, outline="green2", tags='brush')

        print("mouse position = ", x, y)
        print("(x min, x max ; y min, y max) = ", x_min, x_max, y_min, y_max)

        ## box_size is a value given in Angstroms, we need to convert it to pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_half_box_size = int((box_size / angpix_gif)/2) ## since coordinates are given as center, we need to add half the box size to each size of the coordinate

        ## in case the user does not move the mouse after right-clicking, we want to find all clashes in range on this event as well
        erase_coordinates = [] # avoid changing dictionary until after iteration complete
        ## find all coordinates that clash with the brush
        if len(image_coordinates) > 0:
            for coord in image_coordinates:
                if self.check_if_two_ranges_intersect(coord[0] - gif_half_box_size, coord[0] + gif_half_box_size, x_min, x_max): # x0, x1, y0, y1
                    if self.check_if_two_ranges_intersect(coord[1] - gif_half_box_size, coord[1] + gif_half_box_size, y_min, y_max): # x0, x1, y0, y1
                        erase_coordinates.append(coord)

        ## erase all coordinates caught by the brush
        for coord in erase_coordinates:
            del image_coordinates[coord] # remove the coordinate that clashed

        ## update global
        PARAMS['img_coords'] = image_coordinates

        self.draw_image_coordinates()
        return

    def on_right_mouse_release(self, event):
        """ Delete the green brush after the user stops erasing and reset the global flag
        """
        global RIGHT_MOUSE_PRESSED
        RIGHT_MOUSE_PRESSED = False
        self.canvas.delete('brush') # remove any lingering brush marker
        ## update the .BOX file in case coordinates have changed
        self.save_starfile()
        return

    def on_middle_mouse_press(self, event):
        """ When the user clicks the middle mouse, hide all coordinates
        """
        self.canvas.delete('marker')
        self.canvas.delete('particle_positions')
        return

    def on_middle_mouse_release(self, event):
        """ When the middle mouse is released, redraw all coordinates
        """
        self.draw_image_coordinates()
        return

    def save_starfile(self):
        global PARAMS
        ## unpack the global variables for readability
        image_list = PARAMS['img_list']
        n = PARAMS['index']
        image_coordinates = PARAMS['img_coords']
        box_size = PARAMS['box_size']
        img_box_size = PARAMS['img_box_size']
        img_pixel_size_x = PARAMS['img_dimensions'][0]
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        mrc_pixel_size_y = PARAMS['mrc_dimensions'][1]

        # avoid bugging out when hitting 'next img' and no image is currently loaded
        try:
            current_img_base_name = os.path.splitext(image_list[n])[0]

            with open(current_img_base_name + '_CURATED.star', 'w') as f : # NOTE: 'w' overwrites existing file; as compared to 'a' which appends only
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
                for gif_coord in image_coordinates:
                    mrc_coord = image_coordinates[gif_coord]
                    ## new points added on the .GIF with no corresponding .MRC coordinate must interpolate to map the .GIF coordinate onto .MRC
                    ## NOTE: This remapping is imprecise due to uncompression error hence we only do this if it is a 'new_point' in the database
                    if mrc_coord == 'new_point':
                        #### interpolate .MRC coordinate from .GIF position
                        mrc_x, mrc_y = self.gif2star(gif_coord, self.get_scale_factor(PARAMS['mrc_dimensions'], PARAMS['img_dimensions']))
                        f.write("%.2f    %.2f   \t -999     -999.0    -999.0 \n" % (mrc_x, mrc_y))
                    else: # if point is not new, we can just write the original corresponding mrc_coordinate back into the file
                        f.write("%.2f    %.2f   \t -999     -999.0    -999.0 \n" % (mrc_coord[0], mrc_coord[1]))
        except:
            pass
        return

    def on_left_mouse_down(self, event):
        """ Add coordinates to the dictionary at the position of the cursor, then call a redraw.
        """
        global PARAMS

        image_coordinates = PARAMS['img_coords']

        ## in case the user did not explicitly hit the Enter or Return button after editing the boxsize or pixel size entries, refresh their inputs
        self.new_angpix()
        self.new_box_size()

        mouse_position = event.x, event.y

        ## when clicking, check the mouse position against loaded coordinates to figure out if the user is removing a point or adding a point
        if self.is_clashing(mouse_position): # this function will also remove the point if True
            print("CLASHING")
            pass
        else:
            print("Add coordinate: x, y =", mouse_position[0], mouse_position[1])
            x_coord = mouse_position[0]
            y_coord = mouse_position[1]
            image_coordinates[(x_coord, y_coord)] = 'new_point'

        ## update global
        PARAMS['img_coords'] = image_coordinates

        self.draw_image_coordinates()
        return

    def is_clashing(self, mouse_position):
        """
        PARAMETERS
            mouse_position = tuple(x, y); pixel position of the mouse when the function is called
        """
        global PARAMS
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        img_pixel_size_x = PARAMS['img_dimensions'][0]
        angpix = PARAMS['angpix']
        box_size = PARAMS['box_size']
        image_coordinates = PARAMS['img_coords']

        ## Calculate the boundaries to use for the clash check
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_box_width = box_size / angpix_gif ## this is the pixel size of the gif image, we can use this to calculate the size of the box to draw
        gif_box_halfwidth = int( gif_box_width / 2 )

        for (x_coord, y_coord) in image_coordinates:
            # print(" CLASH TEST :: mouse_position = ", mouse_position, " ; existing coord = " , x_coord, y_coord)
            ## check x-position is in range for potential clash
            if x_coord - gif_box_halfwidth <= mouse_position[0] <= x_coord + gif_box_halfwidth:
                ## check y-position is in range for potential clash
                if y_coord - gif_box_halfwidth <= mouse_position[1] <= y_coord + gif_box_halfwidth:
                    ## if both x and y-positions are in range, we have a clash
                    del image_coordinates[(x_coord, y_coord)] # remove the coordinate that clashed
                    ## update global
                    PARAMS['img_coords'] = image_coordinates
                    return True # for speed, do not check further coordinates (may have to click multiple times for severe overlaps)
        return False

    def mark_img(self):
        """ When called, this function updates a list of file names with the current active image. If the current
            img is already marked, it will be 'unmarked' (e.g. removed from the list)
        """
        global PARAMS
        image_list = PARAMS['img_list']
        n = PARAMS['index']
        marked_imgs = PARAMS['marked_imgs']

        current_img = os.path.splitext(image_list[n])[0] ## get the base name of the .GIF file
        # print("Marked imgs = ", marked_imgs)
        print("Mark image = ", current_img)

        if not current_img in marked_imgs:
            marked_imgs.append(current_img)
        else:
            marked_imgs.remove(current_img)

        ## update globals
        PARAMS['marked_imgs'] = marked_imgs
        self.load_img() ## after updating the list, reload the canvas to show a red marker to the user
        return

    def select_all(self, widget):
        """ This function is useful for binding Ctrl+A with
            selecting all text in an Entry widget
        """
        return widget.select_range(0, tk.END)

    def load_file(self):
        """ Permits the system browser to be launched to select an image
            form a directory. Loads the directory and file into their
            respective variables and returns them
        """
        global PARAMS
        # See: https://stackoverflow.com/questions/9239514/filedialog-tkinter-and-opening-files
        fname = askopenfilename(parent=self.master, initialdir=".", title='Select file', filetypes=(
                                            ("All files", "*.*"),
                                            ("Graphics interchange format", "*.gif"),
                                            ("Joint photographic experts group", "*.jpeg;*.jpg")
                                            ))
        if fname:
            try:
                # extract file information from selection
                file_w_path = str(fname)
                file_dir, file_name = os.path.split(str(fname))
                PARAMS['file_dir'] = file_dir
                PARAMS['file_name'] = file_name
                # print("File selected: "+ file_name)
                # print("Active directory: "+ file_dir)

                # erase any previous image list and repopulate it with the new directory
                PARAMS['image_list'] = []
                image_list = self.images_in_dir(file_dir)
                PARAMS['image_list'] = image_list

                # erase any marked image list or particle coordinates loaded into RAM
                PARAMS['marked_imgs'] = []

                # find the index of the selected image in the new list
                n = image_list.index(file_name)
                ## update the global
                PARAMS['index'] = n
                # print(" image index = %s, name = %s" % (n, PARAMS['image_list'][n]))

                ## redraw canvas items with updated global values as the given image index
                self.load_img()

            except:
                showerror("Open Source File", "Failed to read file\n'%s'" % fname)
            return

    def reset_globals(self):
        """ One-stop function for resetting global parameters that often neeed to be reset
            when conditions/data changes.
        """
        global PARAMS
        PARAMS['img_coords'] = {}
        PARAMS['img_box_size'] = 0
        return

    def next_img(self, direction):
        """ Increments the current image index based on the direction given to the function.
        """
        global PARAMS
        n = PARAMS['index']
        image_list = PARAMS['img_list']
        file_dir = PARAMS['file_dir']
        image_coordinates = PARAMS['img_coords']

        ## save particles into boxfile, if coordinates are present
        if len(image_coordinates) > 0 :
            self.save_starfile()

        if file_dir == '.':
            file_dir=os.getcwd()
            try:
                self.current_dir.config(text=file_dir + "/")
            except:
                pass
        if direction == 'right':
            n += 1
            # reset index to the first image when going past the last image in the list
            if n > len(image_list)-1 :
                n = 0
        if direction == 'left':
            n -= 1
            # reset index to the last image in the list when going past 0
            if n < 0:
                n = len(image_list)-1
        ## update global
        PARAMS['index'] = n

        # update image list in case files have been added/removed
        image_list = []
        image_list = self.images_in_dir(file_dir)
        ## update global
        PARAMS['img_list'] = image_list

        ## clear global variables for redraw
        self.reset_globals()

        ## load image with index 'n'
        self.load_img()
        return

    def load_img(self, input_img = None):
        """ Load image with specified index
        PARAMETERS
            index = int(); tied to global 'n' variable, indicating which image to load from the list found in the directory
            input_img = np.array; optional grayscale image (0 - 255) to load instead of using the index
        RETURNS
            Void
        """
        global PARAMS, IMAGE_LOADED
        n = PARAMS['index']
        image_list = PARAMS['img_list']
        marked_imgs = PARAMS['marked_imgs']
        img_pixel_size_x = PARAMS['img_dimensions'][0] # PARAMS['img_pixel_size_x']
        img_pixel_size_y = PARAMS['img_dimensions'][1]
        file_dir = PARAMS['file_dir']
        RESIZE_IMG = PARAMS['RESIZE_IMG']
        img_resize_percent = PARAMS['img_resize_percent']

        ## force a refresh on all canvas objects based on changing global variables
        self.canvas.delete('marker')
        self.canvas.delete('particle_positions')

        image_w_path = file_dir + "/" + image_list[n]

        # update label widget
        self.input_text.delete(0, tk.END)
        self.input_text.insert(0,image_list[n])

        ## check if an eplicit image was passed in, otherwise load the image as usual
        if input_img is None:
            # load image onto canvas object using PhotoImage
            with PIL_Image.open(image_w_path) as im:
                if RESIZE_IMG:
                    new_dimensions = self.get_resized_dimensions(img_resize_percent, im.size)
                    im = im.resize(new_dimensions)
                    print(" Resize image to", new_dimensions)

                im = im.convert('L') ## make grascale
                self.current_img = ImageTk.PhotoImage(im)
                current_im_data = np.asarray(im)
                PARAMS['original_img_data'] = current_im_data
                PARAMS['current_img_data'] = current_im_data

        else:
            ## load the supplied image
            PIL_img = PIL_Image.fromarray(input_img.astype(np.uint8))  #.convert('L')
            self.current_img = ImageTk.PhotoImage(PIL_img)
            current_im_data = input_img.astype(np.uint8)
            PARAMS['current_img_data'] = current_im_data

        # self.current_img = PhotoImage(file=image_w_path)
        self.display = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_img)
        self.canvas.display = self.display

        ## update the global flag
        IMAGE_LOADED = True;

        ## resize canvas to match new image
        x,y = self.current_img.width(), self.current_img.height()
        self.canvas.config(width=x, height=y)
        PARAMS['img_dimensions'] = (x, y)

        base_image_name = os.path.splitext(image_list[n])[0] ## get the base name of the .GIF file

        ## add an inset red border to the canvas depending if the file name exists in a given list
        if base_image_name in marked_imgs:
            marker_rect = self.canvas.create_rectangle(x-10,y-10, 10, 10, outline='red', width=10, tags='marker')

        ## update coordinates in buffer only if we are loading a new image, not if we are passing in a modified image
        if input_img is None:
            ## empty any pre-existing image coordinates in memory
            image_coordinates = {}

            if len(image_coordinates) == 0: ## avoid overwriting an existing image_coordinates dictionary if it is already present
                counter = 0
                star_coordinate_file = ""
                ## to find matching files we need precise names to look for, set them up here:
                match_file1 = base_image_name + ".star"
                match_file2 = base_image_name + "_manualpick.star"
                match_file3 = base_image_name + "_CURATED.star"
                # print("Match file names = %s, %s, %s" % (match_file1, match_file2, match_file3))

                ## find the matching star file if it exists
                for fname in os.listdir(file_dir): ## iterate over the directory
                    if fname == match_file1 or fname == match_file2 or fname == match_file3:
                        # print("MATCH: %s -> %s" % (fname, image_list[n]))
                        counter += 1
                        star_coordinate_file = fname
                        if counter > 1: print(">>> WARNING: Multiple .STAR files found for this image (e.g. multiple files match: " + base_image_name + "*.star)")
                        ## This program writes out ..._CURATED.star files, if we find one - use that over all other available .STAR files
                        if star_coordinate_file[-13:] == "_CURATED.star": break
                ## if a star file is found, load its coordinates
                # print(" STAR FILE USED FOR COORDS = ", star_coordinate_file)
                if (star_coordinate_file != ""):
                    self.read_coords_from_star(star_coordinate_file)

        self.draw_image_coordinates()
        return

    def is_image(self, file):
        """ For a given file name, check if it has an appropriate suffix.
            Returns True if it is a file with proper suffix (e.g. .gif)
        PARAMETERS
            file = str(); name of the file (e.g. 'test.jpg')
        """
        image_formats = [".gif", ".jpg", ".jpeg"]
        for suffix in image_formats:
            if suffix in file:
                return True
        return False

    def images_in_dir(self, path) :
        """ Create a list object populated with the names of image files present
        PARAMETERS
            path = str(), path to the directory with images to view
        """
        image_list = []
        for file in sorted(os.listdir(path)):
            if self.is_image(file):
                image_list.append(file)
        return image_list

    def choose_img(self):
        """ When called, finds the matching file name from the current list and
            loads its image and index
        """
        global PARAMS
        image_list = PARAMS['img_list']
        n = PARAMS['index']
        user_input = self.input_text.get().strip()
        if user_input in image_list:
            n = image_list.index(user_input)
            ## update global index
            PARAMS['index'] = n
            self.load_img()
        else:
            self.input_text.delete(0, tk.END)
            self.input_text.insert(0,"File not found.")
        self.canvas.focus_set()

    def write_marked(self, file="marked_imgs.txt"):
        """ Write marked files (mark files with hotkey 'd') into a file
        """
        ## save a settings as well
        self.save_settings()
        global PARAMS
        marked_imgs = PARAMS['marked_imgs']
        image_coordinates = PARAMS['img_coords']
        ## if present, determine what entries might already exist in the target file (e.g. if continuing from a previous session)
        existing_entries = []
        if os.path.exists(file):
            with open(file, 'r') as f :
                for line in f:
                    existing_entries.append(line.strip())

        ## write new marked images into file, if any present
        with open(file, 'w') as f :
            counter = 0
            for marked_img in marked_imgs:
                counter += 1
                ## write all marked_img names into the file from RAM
                f.write("%s\n" % marked_img)
            print(" >> %s entries written into 'marked_imgs.txt'" % counter)

        ## indicate which images were dropped from the previous file
        for existing_entry in existing_entries:
            if not existing_entry in marked_imgs:
                print(" ... %s was removed from previous entries after rewriting file" % existing_entry)

        ## also save current image particle coordinates if they are present
        if len(image_coordinates) > 0:
            self.save_starfile()

    def load_marked_filelist(self):
        global PARAMS
        marked_imgs = PARAMS['marked_imgs']
        n = PARAMS['index']

        ## load selected file into variable fname
        fname = askopenfilename(parent=self.master, initialdir="./", title='Select file', filetypes=( ("File list", "*.txt"),("All files", "*.*") ))
        if fname:
            try:
                ## extract file information from selection
                logfile_path = str(fname)

                ## parse logfile into program
                with open(logfile_path, 'r') as file_obj :
                    for line in file_obj:
                        ## ignore header lines indicated by hash marks
                        if line[0] == '#':
                            continue
                        ## parse each line with space delimiter into a list using .split() function (e.g. img_name note -> ['img_name', 'note'])
                        column = line.split()
                        ## eliminate empty lines by removing length 0 lists
                        if len(column) == 0:
                            continue
                        ## in cases where multiple entries exist per line, take only the first entry
                        img_name = column[0]
                        # mic_name = os.path.splitext(column[0])[0] # os module path.splitext removes .MRC from input name

                        ## skip adding entry to marked list if already present (e.g. duplicates)
                        if img_name in marked_imgs:
                            continue
                        ## write entry into dictionary
                        marked_imgs.append(img_name)
                        PARAMS['marked_imgs'] = marked_imgs

            except:
                showerror("Open Source File", "Failed to read file\n'%s'" % fname)

            self.load_img() ## reload image in case it has now been marked

            return

    def draw_image_coordinates(self):
        """ Read the global variable list of coordinates with gif and box files associated via a dictionary format, draw all gif coordinates present (regardless if they have associated box coordinates.
        """
        global PARAMS
        image_coordinates = PARAMS['img_coords']
        box_size = PARAMS['box_size']
        img_pixel_size_x = PARAMS['img_dimensions'][0]
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][1]
        angpix = PARAMS['angpix']

        ## delete any pre-existing coordinates if already drawn
        self.canvas.delete('particle_positions')

        ## box_size is a value given in Angstroms, we need to convert it to pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_box_width = box_size / angpix_gif ## this is the pixel size of the gif image, we can use this to calculate the size of the box to draw
        gif_box_halfwidth = int( gif_box_width / 2 )

        # print(" ANGPIX = ", angpix, " ; GIF_ANGPIX = " , angpix_gif, " ; SCALE FACTOR = ", scale_factor)

        for coordinate in image_coordinates:
            ## each coordinate is the center of a box, thus we need to offset by half the gif_box_width pixel length to get the bottom left and top right of the rectangle
            x0 = coordinate[0] - gif_box_halfwidth
            y0 = coordinate[1] - gif_box_halfwidth
            x1 = coordinate[0] + gif_box_halfwidth
            y1 = coordinate[1] + gif_box_halfwidth #y0 - img_box_size # invert direction of box to take into account x0,y0 are at bottom left, not top left
            self.canvas.create_rectangle(x0, y0, x1, y1, outline='red', width=1, tags='particle_positions')

    def header_length(self, file):
        """ For an input .STAR file, define the length of the header and
            return the last line in the header. Header length is determined by
            finding the highest line number starting with '_' character
        """
        with open(file, 'r') as f :
            line_num = 0
            header_lines = []
            for line in f :
                line_num += 1
                first_character = ""
                line = line.strip() # remove empty spaces around line
                line_to_list = line.split() # break words into indexed list format
                # ignore empty lines
                if len(line) == 0 :
                    continue
                first_character = list(line_to_list[0])[0]
                if first_character == '_':
                    header_lines.append(line_num)
            return max(header_lines)

    def find_star_column(self, file, column_type, header_length) :
        """ For an input .STAR file, search through the header and find the column numbers assigned to a given column_type (e.g. 'rlnMicrographName', ...)
        """
        column_num = None # initialize variable for error handling
        with open(file, 'r') as f :
            line_num = 0
            for line in f :
                line_num += 1
                ## extract column number for micrograph name
                if column_type in line :
                    column_num = int(line.split()[1].replace("#",""))
                ## search header and no further to find setup values
                if line_num >= header_length :
                    ## handle error case where input .STAR file is missing a necessary rlnColumn type
                    if column_num is None :
                        print("Input .STAR file: %s, is missing a column for: %s" % (file, column_type) )
                        sys.exit()
                    else:
                        return column_num

    def find_star_info(self, line, column):
        """ For a given .STAR file line entry, extract the data at the given column index.
            If the column does not exist (e.g. for a header line read in), return 'False'
        """
        # break an input line into a list data type for column-by-column indexing
        line_to_list = line.split()
        try:
            column_value = line_to_list[column-1]
            return column_value
        except:
            return False

    def auto_contrast(self):
        """ Use the auto_contrast function on the loaded image
        """
        global PARAMS
        im = PARAMS['current_img_data']
        ## use the image processing functions to modify the desired img
        im = image_handler.auto_contrast(im)

        ## load the modified img onto the canvas
        self.load_img(im)
        return

    def contrast_by_selected_particles(self):
        """ Use the picked particle coordinates to define a working intensity range min/max. Any pixles outside
            of this range are set to white.
        """
        global PARAMS
        image_coordinates = PARAMS['img_coords']
        mrc_pixel_size_x = PARAMS['mrc_dimensions'][0]
        img_pixel_size_x = PARAMS['img_dimensions'][0]
        angpix = PARAMS['angpix']
        box_size = PARAMS['box_size']
        im = PARAMS['current_img_data']

        ## box_size is a value given in Angstroms, we need to convert it to pixels
        scale_factor = mrc_pixel_size_x / img_pixel_size_x
        angpix_gif = angpix * scale_factor
        gif_box_width = int(box_size / angpix_gif) ## this is the pixel size of the gif image, we can use this to calculate the size of the box to draw

        ## extract the particle images from the centered coordinates
        extracted_imgs = image_handler.extract_boxes(im, gif_box_width, image_coordinates, DEBUG = True)
        min, max = image_handler.find_intensity_range(extracted_imgs)
        ## whiten outliers so we can apply new contrast to it
        im = image_handler.whiten_outliers(im, min, max)

        ## use the image processing functions to modify the desired img
        im = image_handler.sigma_contrast(im, 1) ## let the user adjust the sigma value?
        # im = image_handler.gaussian_blur(im, 1.5)

        ## load the modified img onto the canvas
        self.load_img(im)

        return

    def gaussian_blur(self):
        global PARAMS
        im = PARAMS['current_img_data']
        im = image_handler.gaussian_blur(im, 1.5)
        self.load_img(im)
        return

    def local_contrast(self):
        global PARAMS
        ## update box size globals before running filtering
        self.new_box_size()

        img_box_size = PARAMS['img_box_size']
        im = PARAMS['current_img_data']
        im = image_handler.local_contrast(im, img_box_size, DEBUG = True)
        self.load_img(im)
        return

    def toggle_negative_stain(self):
        if self.NEGATIVE_STAIN.get() == True:
            print("Negative stain mode is ON")
        else:
            print("Negative stain mode if OFF")
        return

    def bool_img(self, cutoff, im_array = None):
        global PARAMS
        current_im_data = PARAMS['current_img_data']
        if im_array is None:
            im = image_handler.bool_img(current_im_data, cutoff)
        else:
            im = image_handler.bool_img(im_array, cutoff)

        self.load_img(im)
        return

    def autopick(self, min_area = None, max_area = None, input_img = None, INVERT = None):
        global PARAMS
        ## update necessary globals before running
        self.new_box_size()
        img_box_size = PARAMS['img_box_size']
        if input_img is None:
            ## sanity check an image is loaded into buffer
            try:
                # current_im_data.any()
                input_img = PARAMS['current_img_data']
            except:
                print("Abort autopick :: Image not loaded")
                return

        ## use default setup if no min or max area is given
        if min_area is None:
            min_area = int((img_box_size * img_box_size) / 4)
            print(" Using default min_area for autopicking = %s" % min_area)
        if max_area is None:
            max_area = int(img_box_size * img_box_size * 1.5)
            print(" Using default max_area for autopicking = %s" % max_area)

        ## determine if we should invert the image for autopicking (autopicker picks white peaks)
        if INVERT is None:
            if self.NEGATIVE_STAIN.get() == True:
                invert_img = False
            else:
                invert_img = True
        elif not isinstance(INVERT, bool):
            print("INVERT parameter supplied was NOT a boolean! Exiting autopick.")
            return
        else:
            invert_img = INVERT

        autopicked_coords = image_handler.find_local_peaks(input_img, min_area, max_area, INVERT = invert_img, DEBUG = True)

        ## WIP: need a way to resolve close coordinates that are closer than a given threshold

        # reset the image_coordinates variable and repopulate it below
        image_coordinates = dict()

        ## pass the new coordinates into the appropriate data structure
        for coord in autopicked_coords:
            image_coordinates[coord] = 'new_point'
        ## update global
        PARAMS['img_coords'] = image_coordinates

        ## redraw data on screen
        self.draw_image_coordinates()

        return

    def clear_coordinates(self):
        global PARAMS #image_coordinates
        print(" Clear cached coordinates")
        # reset the image_coordinates variable and repopulate it below
        PARAMS['img_coords'] = dict()
        ## redraw data on screen
        self.draw_image_coordinates()
        return

    def default_autopick(self):
        """ Some testing has shown that decent autopicking results are attained using the following
            image processing steps for autopicking from a raw jpeg img
        """
        global PARAMS
        ## update img_box_size before running
        self.new_box_size()

        img_box_size = PARAMS['img_box_size']
        image_coordinates = PARAMS['img_coords']
        current_im_data = PARAMS['current_img_data']

        ## sanity check an image is loaded into buffer
        try:
            current_im_data.any()
        except:
            print("Abort naive_autopick :: Image not loaded")
            return

        im = PARAMS['current_img_data']
        im = image_handler.local_contrast(im, img_box_size, DEBUG = True)
        im = image_handler.gaussian_blur(im, 1.5, DEBUG = True)
        im = image_handler.auto_contrast(im, DEBUG = True)
        im = image_handler.bool_img(im, 90, DEBUG = True)

        ## run the autopicker on the processed image above
        self.autopick(input_img = im)

        return

class BoolImgPanel(MainUI):
    """ Panel GUI for manipulating image to generate a suitable boolean image
    """
    def __init__(self, mainUI, input_img): # Pass in the main window as a parameter so we can access its methods & attributes
        self.mainUI = mainUI # Make the main window an attribute of this Class object
        self.panel = tk.Toplevel() # Make this object an accessible attribute
        self.panel.title('Apply boolean cutoff')
        self.panel.geometry('430x64')

        ## when the panel is opened, cache the input image
        self.cached_im_data = np.copy(input_img)

        ## Define widgets
        self.cutoff_slider = tk.Scale(self.panel, from_=0, to=255, orient= tk.HORIZONTAL, length = 250, sliderlength = 20)
        self.cutoff_slider.set(100)
        self.apply_button = tk.Button(self.panel, text="Apply", command= lambda: mainUI.bool_img(self.cutoff_slider.get(), self.cached_im_data), width=10)
        self.undo_button = tk.Button(self.panel, text="Undo", command= lambda: mainUI.load_img(self.cached_im_data), width=10)

        ## Pack widgets
        self.cutoff_slider.grid(column=1, row=1)
        self.apply_button.grid(column=2, row=1, sticky = tk.W)
        self.undo_button.grid(column=3, row=1, sticky = tk.W)

        ## Add some hotkeys for ease of use
        self.panel.bind('<Left>', lambda event: self.cutoff_slider.set(self.cutoff_slider.get() - 1))
        self.panel.bind('<Right>', lambda event: self.cutoff_slider.set(self.cutoff_slider.get() + 1))
        self.panel.bind('<Return>', lambda event: mainUI.bool_img(self.cutoff_slider.get(), self.cached_im_data))
        self.panel.bind('<KP_Enter>', lambda event: mainUI.bool_img(self.cutoff_slider.get(), self.cached_im_data)) # numpad 'Return' key

        ## Set focus to the panel
        self.panel.focus()

        ## add an exit function to the closing of this top level window
        self.panel.protocol("WM_DELETE_WINDOW", self.close)
        return

    def close(self):
        ## unset the panel instance before destroying this instance
        self.mainUI.boolImgPanel_instance = None
        ## destroy this instance
        self.panel.destroy()
        return

class AutopickPanel(MainUI):
    """ Panel GUI for user options for autopicking
    """
    def __init__(self, mainUI): # Pass in the main window as a parameter so we can access its methods & attributes
        self.mainUI = mainUI # Make the main window an attribute of this Class object
        self.panel = tk.Toplevel() # Make this object an accessible attribute
        self.panel.title('Autopicking')
        self.panel.geometry('400x200')

        ## Grab variables for setup
        global PARAMS
        img_box_size = PARAMS['img_box_size']
        img_box_area = int(img_box_size * img_box_size)
        print(" Current box size & area = (%s, %s) pixels" % (img_box_size, img_box_area))

        ## Store the original image and the input images into buffer so we can swap them at will
        original_img = PARAMS['original_img_data']
        input_img = PARAMS['current_img_data']

        ## Define widgets
        ## 1. min area slider
        self.min_area_label = tk.Label(self.panel, text = 'Min area (%)', anchor = tk.S, font = ('Helvetica', '11'))
        self.min_area_slider = tk.Scale(self.panel, from_=0, to=100, orient= tk.HORIZONTAL, length = 250, sliderlength = 20)
        self.min_area_slider.set(25)
        ## 2. max area slider
        self.max_area_label = tk.Label(self.panel, text = 'Max area (%)', anchor = tk.S, font = ('Helvetica', '11'))
        self.max_area_slider = tk.Scale(self.panel, from_=0, to=200, orient= tk.HORIZONTAL, length = 250, sliderlength = 20)
        self.max_area_slider.set(150)
        ## 3. buttons
        # self.autopick_button = tk.Button(self.panel, text="Autopick", font = ('Helvetica', '12'), command= lambda: mainUI.autopick(self.min_area_slider.get(), self.max_area_slider.get()), width=10)
        self.autopick_button = tk.Button(self.panel, text="Autopick", font = ('Helvetica', '12'), command = lambda: self.submit_autopicker_job(input_img, img_box_area), width=10)
        self.load_original_img_button = tk.Button(self.panel, text="Show raw img", font = ('Helvetica', '9'), command = lambda: self.display_selected_img(original_img), width=10)
        self.load_input_img_button = tk.Button(self.panel, text="Show input img", font = ('Helvetica', '9'), command = lambda: self.display_selected_img(input_img), width=10)
        ## 4. negative stain option
        self.PICK_WHITE_PEAKS = tk.BooleanVar(self.panel, False)
        self.white_peak_toggle = tk.Checkbutton(self.panel, text='Pick white peaks?', variable=self.PICK_WHITE_PEAKS, onvalue=True, offvalue=False)


        ## Pack widgets
        self.min_area_label.grid(column = 0, row = 1, sticky = tk.S)
        self.min_area_slider.grid(column=1, row=1)
        self.max_area_label.grid(column = 0, row = 2, sticky = tk.S)
        self.max_area_slider.grid(column=1, row=2)
        self.autopick_button.grid(column=0, row=3, padx = 20, pady=10)
        self.white_peak_toggle.grid(column = 1, row = 3)
        self.load_original_img_button.grid(column = 0, row = 4)
        self.load_input_img_button.grid(column = 1, row = 4)

        ## Add some hotkeys for ease of use
        # self.panel.bind('<Left>', lambda event: self.cutoff_slider.set(self.cutoff_slider.get() - 1))
        # self.panel.bind('<Right>', lambda event: self.cutoff_slider.set(self.cutoff_slider.get() + 1))
        self.panel.bind('<Return>', lambda event: self.submit_autopicker_job())
        self.panel.bind('<KP_Enter>', lambda event: self.submit_autopicker_job()) # numpad 'Return' key

        ## Set focus to the panel
        self.panel.focus()

        ## add an exit function to the closing of this top level window
        self.panel.protocol("WM_DELETE_WINDOW", self.close)

        return

    def close(self):
        ## unset the panel instance before destroying this instance
        self.mainUI.autopickPanel_instance = None
        ## destroy this instance
        self.panel.destroy()
        return


    def display_selected_img(self, im_array):
        """ Tell the mainUI to display the given image data (provided as an np array)
        """
        self.mainUI.load_img(im_array)
        return

    def submit_autopicker_job(self, img_data, current_box_area):
        """ Pass the input parameters back to the mainUI to run the autopicker algorithm
        """
        min_area = int(int(self.min_area_slider.get()) / 100 * current_box_area)
        max_area = int(int(self.max_area_slider.get()) / 100 * current_box_area)
        print("=============================")
        print(" Submit autopick:")
        print("   min_area = %s" % min_area)
        print("   max_area = %s" % max_area)

        ## internally, the autopick algorithm inverts the image to make the black peaks white (since black == 0, and white == 255, `peaks' are white by default). So if we want to pick on white peaks in the input image, we need to stop that internal inversion step manually
        if self.PICK_WHITE_PEAKS.get():
            self.mainUI.autopick(min_area, max_area, img_data, INVERT = False)
        else:
            self.mainUI.autopick(min_area, max_area, img_data, INVERT = True)
        return

class HelpPanel(MainUI):
    """ Panel GUI for instructing the use of this program
    """
    def __init__(self, mainUI): # Pass in the main window as a parameter so we can access its methods & attributes
        self.mainUI = mainUI # Make the main window an attribute of this Class object
        self.panel = tk.Toplevel() # Make this object an accessible attribute
        self.panel.title('Help')
        self.panel.geometry('750x520')

        ###############################################
        ## STRING VARIABLES
        ###############################################
        self.section_title = tk.StringVar()
        self.section_title.set("How to use")
        self.section_mainbody ="""Run this program in a directory of .JPG images (created from motion corrected .MRC files) to curate your dataset. Optionally, will automatically load .STAR coordinates from files matching the name, taking any with *_CURATED.STAR above any other duplicates. Will automatically create a *_CURATED.STAR file if one is not present. Designed to curate datasets in two ways:
  (i) Manually inspecting images and marking those to remove.
        d = mark image (red box will appear over sides of image)
        Ctrl + S = save a 'marked_imgs.txt' file in working directory with a list of marked images
        This file can then be used to remove micrographs (E.g. via Select job in relion)
  (ii) Manually inspecting autopicked coordinates.
        Left click = Select particle (remove selected particle if already selected)
        Middle click = Hide all particle/highlights to see unmarked image below
        Right click = Activate erase brush, hold & drag to erase on-the-fly
        Mouse scrollwheel = Increase/decrease eraser tool brush size
        Ctrl + S = save current image coordinates into a *_CURATED.STAR file.
        Moving from one image to another will automatically execute a save function call as well.
"""
        ###############################################

        subsection_list = ["How to use", "Autopicking"]

        # ## Define widgets
        self.dropdown = ttk.Combobox(self.panel, values = subsection_list)
        self.dropdown.set("Help sections")
        self.dropdown.bind("<<ComboboxSelected>>", lambda event: self.UpdateText())
        self.title_text = tk.Label(self.panel, font=("Helvetica, 16"), textvariable=self.section_title)
        self.section_main_text = tk.Text(self.panel, font=("Helvetica, 13"), height = 22, width = 80)
        self.section_main_text.replace("1.0", tk.END, self.section_mainbody)

        ## Pack widgets
        self.dropdown.grid(column=0, row=0, padx = 10, pady = 10, sticky = tk.W)
        self.title_text.grid(column=0, row=1, sticky = tk.W, padx = 15)
        self.section_main_text.grid(column=0, row=2, padx = 10)

        ## Set focus to the panel
        self.panel.focus()

        ## add an exit function to the closing of this top level window
        self.panel.protocol("WM_DELETE_WINDOW", self.close)

        return

    def close(self):
        ## unset the panel instance before destroying this instance
        self.mainUI.helpPanel_instance = None
        ## destroy this instance
        self.panel.destroy()
        return

    def UpdateText(self):
        selected_section = self.dropdown.get()
        if selected_section == "Autopicking":
            self.subsection_autopicking()
        elif selected_section == "How to use":
            self.subsection_howtouse()

    def subsection_autopicking(self):
        self.section_title.set("Autopicking")
        autopick_mainbody = """The autopicking algorithm works on 'boolean' images (i.e. solid black and white images). Thus, for autopicking to succeed it is important to use the image processing steps to enhance the target signals. Hitting the 'Autopick' button in the main window will attempt to do this using a preset sequence of image processing operations before picking peaks at default thresholds.

Often, the best results can be obtained by manually adjusting the raw image so that particle peaks are highlighted over noise. A typical workflow might be:
  (i) Applying local contrast after setting the box size
  (ii) Applying a soft blur to minimize noise effects
  (iii) Applying a boolean threshold that retains target particles as isolated peaks/islands of black pixels
  (iv) Running autopicking at an optimum min/max area cutoff to avoid peaks due to large contaminants or tiny peaks due to noise.

  Autopicked coordinates can then be cleaned up and used as input for initial template generation in RELION via the *_CURATED.star files."""

        self.section_main_text.replace("1.0", tk.END, autopick_mainbody)

    def subsection_howtouse(self):
        self.section_title.set("How to use")
        self.section_main_text.replace("1.0", tk.END, self.section_mainbody)

##########################
### RUN BLOCK
##########################
if __name__ == '__main__':
    import tkinter as tk
    from tkinter.filedialog import askopenfilename
    from tkinter.messagebox import showerror
    from tkinter import ttk
    import numpy as np
    import os, string, sys
    from PIL import Image as PIL_Image
    from PIL import ImageTk
    import re ## for use of re.findall() function to extract numbers from strings
    import copy

    ## Get the execution path of this script so we can find local modules
    script_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    try:
        sys.path.append(script_path)
        import image_handler #as image_handler
    except :
        print(" ERROR :: Check if image_handler.py script is in same folder as this script and runs without error (i.e. can be compiled)!")

    PARAMS = {
        'index' : 0,
        'img_on_save' : '',
        'current_img_data' : None, ## this is the current img loaded and displayed (with all adjustments)
        'original_img_data': None, ## this is the raw img
        'img_list' : [],
        'file_name' : '',
        'file_dir' : '.',
        'marked_imgs' : [],
        'img_coords' : {},
        'img_dimensions' : (0,0),
        'img_box_size' : -1, ## box size of the particles in pixels of the loaded raw image
        'mrc_dimensions': (4092, 4092),
        'angpix' : 1.94, ## resolution of the .MRC pixel size
        'box_size' : 110, ## box size of the particles in Angstroms
        'RESIZE_IMG' : False,
        'img_resize_percent' : 100 ## e.g. 1 - 100%
    }

    brush_size = 20 # default size of erase brush
    IMAGE_LOADED = False # Flag to check if an image is loaded (to avoid throwing errors)
    RIGHT_MOUSE_PRESSED = False # Flag to implement right-mouse activated brush icon

    root = tk.Tk()
    try:
        icon_path = script_path + '/icon.ico'
        icon = PhotoImage(file= icon_path)
        root.tk.call('wm', 'iconphoto', root._w, icon)
    except:
        print('Could not find: ' + script_path + '/icon.ico')
    app = MainUI(root)
    root.mainloop()
