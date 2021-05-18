from pykml import parser
import simplekml
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiLineString, MultiPolygon
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import shutil
import datetime
from pathlib import Path
from PIL import Image, ImageDraw
from zipfile import ZipFile


class Parser(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.region_data = None
        self.boundary = None
        self.load_coordinates()

    def load_coordinates(self):
        with open(self.file_name) as f:
            folder = parser.parse(f).getroot().Document.Folder

        # Need to check for multiple LineString elements
        _lines = []
        alts = []
        for pm in folder.Placemark:
            _line = []
            alt = None
            for points in pm.LineString.coordinates.text.split():
                lon, lat, alt = points.split(',')
                _line.append((float(lon), float(lat)))
            _lines.append(_line)
            alts.append(float(alt))
        ml = MultiLineString(_lines)
        self.region_data, regions = self.find_regions(ml, alts)
        mlp = MultiPolygon(regions)
        self.boundary = unary_union(mlp.buffer(0.001)).exterior.xy

    @staticmethod
    def find_regions(ml: MultiLineString, alts: list):
        lon_bounds = [ml.bounds[0], ml.bounds[2]]
        lat_bounds = [ml.bounds[1], ml.bounds[3]]
        multi_line_buffered = ml.buffer(0.0001)
        diff_regions = ml.envelope.difference(multi_line_buffered)
        # Pad with zeros if necessary
        if len(diff_regions) > len(alts):
            alts.extend([0.0] * (len(diff_regions) - len(alts)))
        i = 0
        regions = []
        region_data = pd.DataFrame(columns=['lat', 'lon', 'alt', 'region_num'])
        for num, geom in enumerate(diff_regions):
            if any(x in lon_bounds for x in geom.exterior.xy[0]) and \
                    any(y in lat_bounds for y in geom.exterior.xy[1]):
                continue
            else:
                for lon, lat in zip(geom.exterior.xy[0], geom.exterior.xy[1]):
                    regions.append(geom)
                    region_data.loc[i, 'lat'] = lat
                    region_data.loc[i, 'lon'] = lon
                    region_data.loc[i, 'alt'] = alts[num]
                    region_data.loc[i, 'region_num'] = num
                    i += 1

        return region_data, regions

    def plot_boundary(self):
        """
        Plot the set of coordinates read from the "load_coordinates" method
        """
        for region in self.regions:
            plt.plot(*region.exterior.xy)
        plt.show()

    def create_composite_boundary(self, removal_bounds):
        """
        Create a boundary that only contains the wanted area of the kml
        Parameters
        __________
        removal_candidate: Radar
            the radar site chosen for removal
        """
        radar_area = Polygon(removal_bounds.observer[0], removal_bounds.observer[1])
        # overall_area = Polygon(self.coordinates.loc[:, 'latitude'], self.coordinates.loc[:, 'longitude'])


class KmlCreator(object):
    def __init__(self):
        self.__init_constants()
        self.kml = None
        self.kml_filepath = None
        self.__num_arrow_icon_files = 36
        self.__arrow_icons_added = []

    def __init_constants(self):
        self.dummy = 0

    def create_kml(self, kml_filepath):
        self.kml = simplekml.Kml()
        self.kml_filepath = kml_filepath

    @staticmethod
    def __set_point_icon_href(point, shape, color=None, base_shape='paddle'):
        if len(color) < 6:
            if color.lower() == 'red':
                color_prefix = 'red'
            elif color.lower() == 'blue':
                color_prefix = 'blu'
            elif color.lower() == 'green':
                color_prefix = 'grn'
            else:
                color_prefix = 'red'

            if 'circle' in shape.lower():
                base_url = 'http://maps.google.com/mapfiles/kml/shapes/'
                # No colors available
                point.style.iconstyle.icon.href = base_url + 'placemark_circle.png'
            elif 'paddle' in shape.lower():
                base_url = 'http://maps.google.com/mapfiles/kml/paddle/'
                point.style.iconstyle.icon.href = base_url + color_prefix + '-square.png'
            elif 'square' in shape.lower():
                base_url = 'http://maps.google.com/mapfiles/kml/paddle/'
                point.style.iconstyle.icon.href = base_url + color_prefix + '-square-lv.png'
            elif 'arrow' in shape.lower():
                # arrow or arrow:<num>
                if ':' in shape:
                    # arrow:<num>
                    t_list = shape.split(':')
                    arrow_type = int(t_list[1])
                    if (arrow_type < 0) or (arrow_type >= 16):
                        arrow_type = 0
                else:
                    # arrow
                    arrow_type = 0
                base_url = 'http://earth.google.com/images/kml-icons/track-directional/'
                point.style.iconstyle.icon.href = base_url + 'track-' + str(arrow_type) + '.png'
            elif 'test' in shape.lower():
                base_url = 'http://maps.google.com/mapfiles/kml/paddle/8.png'
                point.style.iconstyle.icon.href = base_url
                point.style.iconstyle.color = 'ff32ea1e'
            else:
                # pushpin is default shape
                do_nothing = True
        else:
            if base_shape == 'paddle':
                base_url = 'http://maps.google.com/mapfiles/kml/paddle/'
                if len(shape) > 1:
                    point.style.iconstyle.icon.href = base_url + 'wht-' + shape + '.png'
                else:
                    point.style.iconstyle.icon.href = base_url + shape + '.png'
            else:
                base_url = f'http://maps.google.com/mapfiles/kml/paddle/wht-{shape}-lv'
                point.style.iconstyle.icon.href = base_url + '.png'

            # point.style.iconstyle.color = 'ff' + color
            point.style.iconstyle.color = color

    def add_folder(self, parent_folder=None, name=None):
        if name is None:
            name = 'New Folder'
        if parent_folder is not None:
            new_folder = parent_folder.newfolder(name=name)
        else:
            new_folder = self.kml.newfolder(name=name)
        return new_folder

    def __get_arrow_icon_filepath(self, color, angle_degrees, size_string=None) -> str:
        kml_folder = '.'
        if self.kml_filepath is not None:
            kml_folder = os.path.dirname(self.kml_filepath)
        angle_step = 360.0 / self.__num_arrow_icon_files
        angle_idx = int(angle_degrees/angle_step)
        if size_string is None:
            arrow_filename = 'arrow_%02x%02x%02x_%02d.png' % (color[0], color[1], color[2], angle_idx)
        else:
            arrow_filename = 'arrow_%02x%02x%02x_%02d_%s.png' % (color[0], color[1], color[2], angle_idx, size_string)
        f_path = f'{kml_folder}\\files\\{arrow_filename}'
        return f_path

    def add_arrow_icons_to_kml(self, color=None, dim=None, angle_degrees=None):
        # dim = (w, h)
        kml_folder = os.path.dirname(self.kml_filepath)
        gen_funcs = GenFuncs()
        gen_funcs.create_dir(kml_folder + '\\files')
        use_color = (0, 0, 0)
        if color is not None:
            use_color = (color[0], color[1], color[2])
        angle = 0
        angle_step = 360 / self.__num_arrow_icon_files
        while angle <= 360.0:
            f_path = self.__get_arrow_icon_filepath(use_color, angle)
            fi = ImageFuncs.draw_arrow(size='tiny', fill_color=use_color, outline_color=use_color, angle_degrees=angle)
            angle = int(angle + angle_step)
            if f_path not in self.__arrow_icons_added:
                self.__arrow_icons_added.append(f_path)

    def add_arrow_icon(self, lat, lon, parent_node=None, altitude=None, angle_degrees=0, name=None,
                       description=None, color=None, date_time_string=None, arrow_dim=(8, 16)):
        if color is None:
            color = [0, 0, 0]
        if parent_node is None:
            parent_node = self.kml
        if name is not None:
            pnt = parent_node.newpoint(name=name)
        else:
            pnt = parent_node.newpoint()
        pnt.coord = [(lon, lat)]
        if altitude is not None:
            pnt.coords = [(lon, lat, altitude)]
            pnt.altitudemode = simplekml.AltitudeMode.absolute
            pnt.extrude = 1
        if description is not None:
            pnt.description = description
        if date_time_string is not None:
            pnt.timestamp.when = GenFuncs.datetime_string_to_format(time_string=date_time_string,
                                                                    in_format='1980-01-01%H:%M:%SZ')

        size_string = '%dw%dh' % (arrow_dim[0], arrow_dim[1])
        arrow_icon_path = self.__get_arrow_icon_filepath(color, angle_degrees, size_string=size_string)
        arrow_icon_name = os.path.basename(arrow_icon_path)
        if arrow_icon_path not in self.__arrow_icons_added:
            self.add_arrow_icons_to_kml(color, dim=arrow_dim, angle_degrees=angle_degrees)
        pnt.style.iconstyle.icon.href = 'files/%s' % arrow_icon_name
        return pnt

    def add_point(self, lat, lon, parent_node=None, altitude=None, name=None, description=None,
                  time_stamp=None, shape=None, color=None):
        if parent_node is None:
            parent_node = self.kml
        if name is not None:
            pnt = parent_node.newpoint(name=name)
        else:
            pnt = parent_node.newpoint()

        if altitude is not None:
            pnt.coords = [(lon, lat, altitude)]
            pnt.altitudemode = simplekml.AltitudeMode.absolute
            pnt.extrude = 1
        else:
            pnt.coords = [(lon, lat)]

        if time_stamp is not None:
            pnt.timestamp.when = time_stamp
        if description is not None:
            pnt.description = description
        if shape is not None:
            self.__set_point_icon_href(point=pnt, shape=shape, color=color)

        return pnt

    def add_points(self, lat_lon_list, shape=None, color=None):
        for lat_lon in lat_lon_list:
            if len(lat_lon) > 2:
                self.add_point(lat_lon[0], lat_lon[1], altitude=lat_lon[2], shape=shape, color=color)
            else:
                self.add_point(lat_lon[0], lat_lon[1], shape=shape, color=color)

    def add_diamond(self, lat, lon, size=1, filled=True, parent_node=None,
                    color=None, opacity=100, name=None, description=None):
        """
        This is a special point, made here as tiny polygon. The reason for this is to allow it to be of any color
        as per [R, G, B]
        Parameters
        __________
        lat, lon
        size: int
            None or 1 - 10. (default to 1, which is size of 0.001)
        filled: bool
            Create polygon filled or just outline
        parent_node
        color: list
            [R, G, B]
        opacity: int
            0 (transparent) - 100 (opaque)
        name: str
            Node name
        description: str
            Node popup description
        """
        if size is None:
            size = 1
        size = size * 0.001
        [lat1, lat2, lat3, lat4, lat5] = [lat, (lat + size), lat, (lat-size), lat]
        [lon1, lon2, lon3, lon4, lon5] = [(lon-size), lon, (lon+size), lon, (lon-size)]

    def add_polygon(self, lat_lon_list, filled=True, line_width=1, parent_node=None,
                    color=None, opacity=50, name=None, description=None) -> None:
        """
        Parameters
        __________
        lat_lon_list: list
            [ [lat, lon], [lat, lon], ... ]
        filled: bool
            Create a polygon filled or just outline
        parent_node
        color: list
            [R, G, B]
        opacity: int
            0 (transparent) - 100 (opaque)
        name: str
            Node name
        description: str
            Pop up description box
        """
        if parent_node is None:
            parent_node = self.kml
        if filled:
            pol = parent_node.newpolygon()
        else:
            pol = parent_node.newlinestring()
        if name is not None:
            pol.name = name
        if description is not None:
            pol.description = description

        swapped_lat_lon = []
        for lat_lon in lat_lon_list:
            swapped_lat_lon.append((lat_lon[1], lat_lon[0]))
        if filled:
            pol.outerboundaryis.coords = swapped_lat_lon
            pol.style.linestyle.width = 0

            if color is not None:
                rgb_color = simplekml.Color.rgb(color[0], color[1], color[2])
                alpha = int(255 * opacity/100)
                pol.style.polystyle.color = simplekml.Color.changealphaint(alpha, rgb_color)
        else:
            pol.coords = swapped_lat_lon
            pol.style.linestyle.width = line_width

            if color is not None:
                rgb_color = simplekml.Color.rgb(color[0], color[1], color[2])
                alpha = int(255 * opacity/100)
                pol.style.polystyle.color = simplekml.Color.changealphaint(alpha, rgb_color)

    def add_3d_polygon(self, lla_list, filled=True, line_width=1,
                       parent_node=None, color=None, opacity=50, name=None, description=None) -> None:
        """
        Create a 3 dimensional airspace plot
        lla_list:
        """
        pass

    def add_special(self, lat, lon, base_shape, parent_node=None, name=None, description=None,
                    shape=None, color=None):
        """
        Special function for SPA Workgroup kml creation
        """
        # TODO: Make a private method so this isn't repeated in other functions
        # self._valdiate_poitn(lat, lon, shape, color)
        if parent_node is None:
            parent_node = self.kml
        if name is not None:
            pnt = parent_node.newpoint(name=name)
        else:
            pnt = parent_node.newpoint()

        pnt.coords = [(lon, lat)]

        if description is not None:
            pnt.description = description

        if shape is not None:
            self.__set_point_icon_href(point=pnt, shape=shape, color=color, base_shape=base_shape)

        return pnt

    def add_tiles(self, tile_coordinates, line_width=1, parent_node=None,
                  color=None, opacity=50, name=None, description=None) -> None:
        """
        Parameters
        __________
        tile_coordinates: list
            [ [lat, lon, alt], [lat, lon, alt], ... ]
        line_width: int
            width for the outer line of the tile
        parent_node
        color: list
            [R, G, B]
        opacity: int
            0 (transparent) - 100 (opaque)
        name: str
            None name
        description: str
            Pop up description box
        """
        if parent_node is None:
            parent_node = self.kml
        for row in tile_coordinates:
            pol = parent_node.newpolygon()
            if name is not None:
                pol.name = name
            if description is not None:
                pol.description = description
            pol.outerboundaryis.coords = row
            pol.style.linestyle.width = 1
            if color is not None:
                rgb_color = simplekml.Color.rgb(color[0], color[1], color[2])
                alpha = int(255 * opacity/100)
                pol.style.polystyle.color = simplekml.Color.changealphaint(alpha, rgb_color)
                pol.style.linestyle.color = simplekml.Color.changealphaint(alpha, rgb_color)

    def save(self, pretty=True):
        kml_folder = os.path.dirname(self.kml_filepath)
        if (len(kml_folder) == 0) or (kml_folder is None):
            kml_folder = '.'

        kmz_file_path = self.kml_filepath.replace('.kml', '.kmz')
        kml_file_path = self.kml_filepath.replace('.kmz', '.kml')

        kmz_file_name = os.path.basename(kmz_file_path)
        kml_file_name = os.path.basename(kml_file_path)

        cur_dir = os.getcwd()
        gen_funcs = GenFuncs()
        if pretty:
            self.kml.save(kml_file_name)
        else:
            fp = gen_funcs.open_file(kml_file_name, 'w')
            fp.write(str(self.kml.document))
            fp.close()

        if ('.kmz' in self.kml_filepath) or (len(self.__arrow_icons_added) > 0):
            gen_funcs.delete_file(kmz_file_name)
            with ZipFile(kmz_file_name, 'w') as zip:
                if len(self.__arrow_icons_added) > 0:
                    for arrow_icon_file in self.__arrow_icons_added:
                        f_name = 'files\\' + os.path.basename(arrow_icon_file)
                        zip.write(kml_file_name)

            gen_funcs.delete_file(kml_file_name)
            gen_funcs.delete_dir('files')
            return_val = kml_file_path
        else:
            return_val = kml_file_path
        os.chdir(cur_dir)
        return return_val


class GenFuncs(object):
    def __init__(self):
        pass

    @staticmethod
    def open_file(file_path, mode):
        fp = None
        err = None
        try:
            fp = open(Path(file_path), mode)
        except OSError as e:
            err = str(e)

        assert err is None, err  #  Print the error if one occurs
        return fp

    def does_file_exist(self, file_path):
        return self.does_path_exist(Path(file_path))

    def does_dir_exist(self, dir_path):
        return self.does_path_exist(Path(dir_path))

    @staticmethod
    def does_path_exist(file_path) -> bool:
        # isdir and isfile will ensure it follows symlinks
        # return os.path.exists(file_path)
        return (os.path.isdir(Path(file_path))) or (os.path.isfile(Path(file_path)))

    @staticmethod
    def create_dir(dir_path):
        err = None
        if len(dir_path) > 0:
            try:
                os.makedirs(Path(dir_path), exist_ok=True)
            except OSError as e:
                err = str(e) + f'({Path(dir_path)})'
            assert err is None, err

    @staticmethod
    def split_filepath(in_path) -> dict:
        head_tail = os.path.split(Path(in_path))
        return {'path': head_tail[0], 'file_name': head_tail[1]}

    @staticmethod
    def split_filename(in_file) -> dict:
        name_ext = os.path.splitext(in_file)
        return {'name': name_ext[0], 'ext': name_ext[1]}

    @staticmethod
    def delete_file(file_path):
        if os.path.exists(Path(file_path)):
            os.remove(Path(file_path))

    @staticmethod
    def delete_dir(dir_path):
        # Dir and children recursively
        if os.path.exists(Path(dir_path)):
            shutil.rmtree(Path(dir_path))

    @staticmethod
    def convert_time_string_to_milliseconds(time_string) -> int:
        time_list = time_string.split(':')
        idx = 0
        hh = 0
        mm = 0
        ss_nnn = 0.0
        if len(time_list) >= 3:
            hh = time_list[idx]
            idx += 1
        if len(time_list) >= 2:
            mm = time_list[idx]
            idx += 1
        if len(time_list) >= 1:
            ss_nnn = time_list[idx]

        milli_seconds = int(((float(hh)*3600) + (float(mm)*60) + float(ss_nnn)) * 1000)
        return milli_seconds

    @staticmethod
    def secs_to_time_string(secs) -> str:
        min = int((int(secs)/60))
        sec = int(secs) - int(min*60)
        hr = int(min/60)
        min = min - (hr*60)
        retval = ''
        if hr > 0:
            retval = '%02d:%02d:%02d hours' % (hr,min,sec)
        elif min > 0:
            retval = '%02d:%02d mins' % (min, sec)
        else:
            retval = '%02d secs' % sec

        return retval

    @staticmethod
    def time_now(show_date=True, show_time=True) -> str:
        now = datetime.datetime.now()
        retval = now.strftime('%Y-%m-%d %H:%M:%S')
        if not show_date and show_time:
            retval = now.strftime('%H:%M:%S')

        return retval

    @staticmethod
    def datetime_string_to_format(date_string=None, time_string=None, in_format=None) -> str:
        dd = 0
        mm = 0
        yyyy = 0
        if date_string is not None:
            date_list = date_string.split('/')
            if len(date_list) >= 3:
                mm = int(date_list[0])
                dd = int(date_list[1])
                yyyy = int(date_list[2])

        if time_string is not None:
            hh = 0
            mm = 0
            ss = 0
            nnn = 0
            time_list = time_string.split(':')
            idx = 0
            if len(time_list) >= 3:
                hh = int(time_list[idx])
                idx += 1
            if len(time_list) >= 2:
                mm = int(time_list[idx])
                idx += 1
            if len(time_list) >= 1:
                ss_nnn = time_list[idx].split('.')
                ss = int(ss_nnn[0])
                if len(ss_nnn) > 1:
                    nnn = int(ss_nnn[1])

        d_time = None
        if (date_string is not None) and (time_string is not None):
            d_time = datetime.datetime(year=yyyy, month=mm, day=dd, hour=hh, second=ss, microsecond=nnn*1000)
        elif (date_string is not None) and (time_string is None):
            d_time = datetime.datetime(year=yyyy, month=mm, day=dd)
        elif (date_string is None) and (time_string is not None):
            d_time = datetime.time(hour=hh, minute=mm, second=ss, microsecond=nnn*1000)

        formatted_time_str = None
        if d_time is not None:
            formatted_time_str = d_time.strftime(in_format)

        return formatted_time_str

    @staticmethod
    def csv_split(s1, delim=',') -> list:
        ret_list = []
        if s1 is None:
            return ret_list
        if s1.strip() == '':
            return ret_list

        return s1.split(delim)


class ImageFuncs(object):
    def __init__(self, img_path):
        self.__im__ = None
        self.__orig_im__ = None
        self.__img_path = img_path

    @property
    def img_path(self):
        return self.__img_path

    @img_path.setter
    def img_path(self, value):
        self.__img_path = value
        self.__im__ = Image.open(value)
        self.__orig_im__ = self.__im__

    def reset(self):
        self.__im__ = self.__orig_im__

    @staticmethod
    def show_image(img_path=None, im=None):
        """
        This will open the image using the default file association program
        """
        if img_path is not None:
            im = Image.open(img_path)
        if img_path is None:
            return False
        im.show()

    def show(self, img_path=None):
        ImageFuncs.show_image(img_path, self.__im__)

    @staticmethod
    def save_image(out_img_path, out_format='JPEG', img_path=None, im=None):
        """
        Create an output image file
        If img_path is not specified, im MUST be specified and will be used
        If out_format is not specified, default 'JPEG' format will be used
            For out_formats see: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html
            Common examples are: 'BMP', 'GIF', 'ICO', 'JPEG', 'PNG', 'TIFF'
        """
        if img_path is not None:
            im = Image.open(img_path)
        if im is None:
            return False
        im.save(out_img_path, format=out_format)

    def save(self, out_img_path, out_format='JPEG', in_img_path=None):
        ImageFuncs.save_image(out_img_path, out_format, in_img_path, self.__im__)

    @staticmethod
    def get_image_size(img_path=None, im=None) -> tuple:
        """
        Returns a tuple (width, height) in pixels
        """
        if img_path is not None:
            im = Image.open(img_path)
        if im is None:
            return 0, 0

        return im.size

    def get_size(self):
        return ImageFuncs.get_image_size(im=self.__im__)

    @staticmethod
    def resize_image(img_path=None, im=None, width=None, height=None, retain_aspect=False):
        """
        If retain_aspect is True, and both width and height are given, then only width is used
        """
        if img_path is not None:
            im = Image.open(img_path)
        if im is None:
            return None
        (in_width, in_height) = ImageFuncs.get_image_size(im=im)
        if width is None:
            width = in_width
        if height is None:
            height = in_height
        (use_width, use_height) = (width, height)
        if retain_aspect:
            if width is not None:
                ratio = width / in_width
                use_width = width
                use_height = int(in_height * ratio)
            elif height is not None:
                ratio = height / in_height
                use_width = int(width * ratio)
                use_height = height

        return im.resize((use_width, use_height), Image.ANTIALIAS)

    def resize(self, width=None, height=None, retain_aspect=False):
        self.__im__ = ImageFuncs.resize_image(im=self.__im__, width=width, height=height, retain_aspect=retain_aspect)

    @staticmethod
    def crop_image(img_path=None, im=None, width=None, height=None, align='center'):
        """
        align='center': crop width both sides and height both sides
        align='top': crop width both sides and height bottom
        align='bottom': crop width both sides and height top
        align='left': crop width right and height both sides
        align='right': crop width left and height both sides
        align='top left': crop width right and height bottom
        align='top right': crop width left and height bottom
        align='bottom left': crop width right and height top
        align='bottom right': crop width left and height top
        """
        if img_path is not None:
            im = Image.open(img_path)
            if im is None:
                return None
            (in_width, in_height) = ImageFuncs.get_image_size(im=im)
            if width is None:
                width = in_width
            if height is None:
                height = in_height
            delta_width = (in_width - width)
            delta_height = (in_height - height)

            # Default center crop
            (left, top, right, bottom) = (delta_width/2,
                                          delta_height/2,
                                          (in_width - delta_width/2),
                                          (in_height - delta_height))
            if 'top' in align:
                (top, bottom) = (0, in_height - delta_height)
            if 'bottom' in align:
                (top, bottom) = (delta_height, in_height)
            if 'left' in align:
                (left, right) = (0, in_width - delta_width)
            if 'right' in align:
                (left, right) = (delta_width, in_width)

            return im.crop((left, top, right, bottom))

    def crop(self, width=None, height=None, align='center'):
        self.__im__ = ImageFuncs.crop_image(im=self.__im__, width=width, height=height, align=align)

    @staticmethod
    def rotate_image(img_path=None, im=None, angle_degrees=90, direction='right', expand=True):
        """
        Rotates the image in direction by angle degrees, where 0 = UP
        direction = 'right' or 'left'
        If expand is True, then the size is not truncated on rotate
        """
        if img_path is not None:
            im = Image.open(img_path)
        if im is None:
            return None

        if 'right' in direction:
            angle_degrees = 360 - angle_degrees

        return im.rotate(angle_degrees, expand=expand)

    def rotate(self, angle_degrees=90, direction='right', expand=True):
        self.__im__ = ImageFuncs.rotate_image(im=self.__im__, angle_degrees=angle_degrees,
                                              direction=direction, expand=expand)

    @staticmethod
    def draw_polygon_image(xy_list, im=None, fill_color=(255, 0, 0), outline_color = (0, 0, 255)):
        """
        Specify xy_list as ( (x1, y1), (x2, y2), (x3, y3), .... (xn, yn) )
        """
        (min_x, min_y, max_x, max_y) = (-1, -1, -1, -1)
        for xy in xy_list:
            if (min_x < 0) or (min_x > xy[0]):
                min_x = xy[0]
            if (min_y < 0) or (min_y > xy[1]):
                min_y = xy[1]
            if (max_x < 0) or (max_x < xy[0]):
                max_x = xy[0]
            if (max_y < 0) or (max_y < xy[1]):
                max_y = xy[1]

        width = (max_x - min_x)
        height = (max_y - min_y)
        if im is None:
            im = Image.new('RGBA', (width, height))
        draw = ImageDraw.Draw(im)
        draw.polygon(xy_list, fill=fill_color, outline=outline_color)
        return im

    @staticmethod
    def draw_arrow(im=None, dim=None, size='small',
                   fill_color=(255, 0, 0), outline_color=(0, 0, 255), angle_degrees=90):
        """
            if dim is specified as (width,height):
                size is ignored
            else:
                size == tiny  = (width,height) = (24,12)
                size == small  = (width,height) = (50,25)
                size == medium = (width,height) = (100,50)
                size == large = (width,height) = (200,100)
        """
        if dim is None:
            if 'tiny' in size:
                (width, height) = (8, 16)
            if 'small' in size:
                (width, height) = (16, 32)
            if 'medium' in size:
                (width, height) = (24, 48)
            if 'large' in size:
                (width, height) = (32, 64)
        else:
            (width, height) = dim

        xy_list = ((0, 0), (width, 0), (int(width/2), height), (0, 0))
        arrow_im = ImageFuncs.draw_polygon_image(xy_list, im=im, fill_color=fill_color, outline_color=outline_color)
        # Angle currently pointing downwards, below we rotate it to point up
        arrow_im = ImageFuncs.rotate_image(im=arrow_im, angle_degrees=180)
        # Now the arrow will be rotated correctly to what the user specified
        return ImageFuncs.rotate_image(im=arrow_im, angle_degrees=angle_degrees)


if __name__ == '__main__':
    f = GenFuncs()
    test_num = [5]
    for test in test_num:
        if test == 1:
            """
            Test both 'split' methods
            """
            fs = f.split_filepath('C:\\tmpa\\tmpb\\tmpc\\abcd.out')
            print(f'dir = {fs["path"]}\nfile = {fs["file_name"]}')
            ne = f.split_filename(fs['file_name'])
            print(f'name = {ne["name"]}\next = {ne["ext"]}')
        if test == 2:
            """
            Test the milliseconds conversion
            """
            print(f.convert_time_string_to_milliseconds('14:09:59.236'))
            print(f.convert_time_string_to_milliseconds('09:59.236'))
            print(f.convert_time_string_to_milliseconds('1'))
            print(f.convert_time_string_to_milliseconds('1:0'))
            print(f.convert_time_string_to_milliseconds('1:0:0'))
        if test == 3:
            """
            Test the datetime conversion
            """
            print(f.datetime_string_to_format('1/10/1988', '1:2:3.4', '%d/%m/%Y %H-%M-%S'))
        if test == 4:
            kml = KmlCreator()
            kml.create_kml('test.kml')
            kml.add_point(40.782778, -73.970833,altitude=1000,name="NYC",shape="arrow:0")
            kml.add_point(39.952222, -75.165000,name="PHL",shape="square",color="red")

            kml.add_polygon(
                [(40.782778, -73.970833), (40.782778, -75.165000), (39.952222, -75.165000), (39.952222, -73.970833)],
                color=[0xFF, 0x00, 0x00],
                opacity=45)
            kml.save()
        if test == 5:
            p = Parser('../data/Tracy SFOW.kml')