# -*- coding: utf-8 -*-
"""
Wall Orientation Detection Logic
Bagian dari PrasKaaPyKit - Smart Tag System

Modul ini menjelaskan cara mengetahui orientasi dinding dalam Revit API
untuk keperluan positioning tag yang akurat.
"""

from pyrevit import DB
import math

class WallOrientationHandler:
    """Handler untuk mendeteksi dan mengelola orientasi dinding"""

    def __init__(self, doc):
        self.doc = doc

    def get_wall_orientation(self, wall):
        """
        Mendapatkan orientasi dinding menggunakan Wall.Orientation property

        Args:
            wall (DB.Wall): Objek dinding Revit

        Returns:
            DB.XYZ: Vektor orientasi dinding (normal ke permukaan)
                   Mengarah ke arah hadap dinding
        """
        try:
            # Properti Wall.Orientation langsung dari Revit API
            orientation = wall.Orientation

            # Normalize vektor untuk konsistensi
            orientation = orientation.Normalize()

            return orientation

        except Exception as e:
            print("Error getting wall orientation: {}".format(str(e)))
            return None

    def get_wall_facing_direction(self, wall):
        """
        Mendapatkan arah hadap dinding (arah normal permukaan)

        Args:
            wall (DB.Wall): Objek dinding Revit

        Returns:
            dict: Dictionary berisi:
                - 'orientation': XYZ vector orientasi
                - 'angle': Sudut orientasi dalam derajat (0-360)
                - 'cardinal': Arah kardinal ('N', 'S', 'E', 'W', dll)
        """
        orientation = self.get_wall_orientation(wall)
        if not orientation:
            return None

        # Hitung sudut dari sumbu X positif (East)
        angle_rad = math.atan2(orientation.Y, orientation.X)
        angle_deg = math.degrees(angle_rad)

        # Normalisasi ke 0-360 derajat
        if angle_deg < 0:
            angle_deg += 360

        # Tentukan arah kardinal
        cardinal = self._get_cardinal_direction(angle_deg)

        return {
            'orientation': orientation,
            'angle': angle_deg,
            'cardinal': cardinal
        }

    def _get_cardinal_direction(self, angle):
        """
        Mengkonversi sudut menjadi arah kardinal

        Args:
            angle (float): Sudut dalam derajat (0-360)

        Returns:
            str: Arah kardinal
        """
        directions = [
            ('N', 0, 22.5),
            ('NE', 22.5, 67.5),
            ('E', 67.5, 112.5),
            ('SE', 112.5, 157.5),
            ('S', 157.5, 202.5),
            ('SW', 202.5, 247.5),
            ('W', 247.5, 292.5),
            ('NW', 292.5, 337.5),
            ('N', 337.5, 360)
        ]

        for direction, min_angle, max_angle in directions:
            if min_angle <= angle < max_angle:
                return direction

        return 'N'  # Default

    def calculate_tag_position(self, wall, offset_mm=100):
        """
        Menghitung posisi tag berdasarkan orientasi dinding

        Args:
            wall (DB.Wall): Objek dinding Revit
            offset_mm (float): Offset dalam millimeter

        Returns:
            DB.XYZ: Posisi tag yang optimal
        """
        try:
            # Dapatkan orientasi
            orientation = self.get_wall_orientation(wall)
            if not orientation:
                return None

            # Dapatkan midpoint dinding
            midpoint = self._get_wall_midpoint(wall)
            if not midpoint:
                return None

            # Konversi offset ke feet (Revit unit)
            offset_feet = offset_mm / 304.8  # 1 mm = 1/304.8 feet

            # Hitung posisi tag: midpoint + (orientation * offset)
            tag_position = midpoint.Add(orientation.Multiply(offset_feet))

            return tag_position

        except Exception as e:
            print("Error calculating tag position: {}".format(str(e)))
            return None

    def _get_wall_midpoint(self, wall):
        """
        Mendapatkan titik tengah dinding

        Args:
            wall (DB.Wall): Objek dinding Revit

        Returns:
            DB.XYZ: Titik tengah dinding
        """
        try:
            # Dapatkan location curve
            location_curve = wall.Location
            if not isinstance(location_curve, DB.LocationCurve):
                return None

            curve = location_curve.Curve

            # Untuk line, midpoint adalah rata-rata start dan end
            if isinstance(curve, DB.Line):
                start = curve.GetEndPoint(0)
                end = curve.GetEndPoint(1)
                midpoint = DB.XYZ(
                    (start.X + end.X) / 2,
                    (start.Y + end.Y) / 2,
                    (start.Z + end.Z) / 2
                )
                return midpoint

            # Untuk curve lainnya, gunakan Evaluate
            try:
                param_mid = curve.GetEndParameter(0) + (curve.GetEndParameter(1) - curve.GetEndParameter(0)) / 2
                midpoint = curve.Evaluate(param_mid, False)
                return midpoint
            except:
                # Fallback ke start point
                return curve.GetEndPoint(0)

        except Exception as e:
            print("Error getting wall midpoint: {}".format(str(e)))
            return None

    def is_wall_facing_positive_direction(self, wall, view_direction=None):
        """
        Mengecek apakah dinding menghadap ke arah positif

        Args:
            wall (DB.Wall): Objek dinding Revit
            view_direction (DB.XYZ): Arah view (opsional)

        Returns:
            bool: True jika menghadap positif
        """
        orientation = self.get_wall_orientation(wall)
        if not orientation:
            return False

        if view_direction:
            # Cek dot product dengan view direction
            dot_product = orientation.DotProduct(view_direction)
            return dot_product > 0
        else:
            # Default: cek dengan sumbu X positif (East)
            return orientation.X > 0

# Contoh penggunaan dalam Smart Tag System
def example_wall_orientation_usage():
    """
    Contoh penggunaan WallOrientationHandler dalam Smart Tag
    """
    from pyrevit import revit
    doc = revit.doc

    # Inisialisasi handler
    orientation_handler = WallOrientationHandler(doc)

    # Dapatkan dinding dari selection
    walls = []
    for element_id in revit.uidoc.Selection.GetElementIds():
        element = doc.GetElement(element_id)
        if isinstance(element, DB.Wall):
            walls.append(element)

    # Proses setiap dinding
    for wall in walls:
        # Dapatkan orientasi lengkap
        facing_info = orientation_handler.get_wall_facing_direction(wall)

        if facing_info:
            print("Wall ID: {}".format(wall.Id))
            print("Orientation: ({:.3f}, {:.3f}, {:.3f})".format(
                facing_info['orientation'].X,
                facing_info['orientation'].Y,
                facing_info['orientation'].Z
            ))
            print("Angle: {:.1f}°".format(facing_info['angle']))
            print("Cardinal Direction: {}".format(facing_info['cardinal']))

            # Hitung posisi tag
            tag_pos = orientation_handler.calculate_tag_position(wall, offset_mm=100)
            if tag_pos:
                print("Tag Position: ({:.3f}, {:.3f}, {:.3f})".format(
                    tag_pos.X, tag_pos.Y, tag_pos.Z
                ))
            print("---")

if __name__ == "__main__":
    example_wall_orientation_usage()