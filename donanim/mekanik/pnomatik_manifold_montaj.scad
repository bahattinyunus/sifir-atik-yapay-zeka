// Sıfır Atık YZ - 5 Kanallı Pnömatik Solenoid Manifold Montaj Braketi
// 2020 Alüminyum Sigma Profile ve standart 1/4" 5'li manifold bloğuna uyumludur.
// OpenSCAD ile düzenlenebilir veya STL formatına ihraç edilip 3D yazıcıdan basılabilir.

$fn = 60;

manifold_width = 35;
manifold_length = 135;
thickness = 5;

module manifold_bracket() {
    difference() {
        cube([manifold_length, manifold_width, thickness]);

        // Manifold sabitleme delikleri (M4 Cıvata, 110mm aralık)
        translate([12.5, manifold_width/2, -1])
            cylinder(h = thickness + 2, d = 4.3);
        translate([manifold_length - 12.5, manifold_width/2, -1])
            cylinder(h = thickness + 2, d = 4.3);

        // 2020 Sigma Profil Montaj Slotları (M4 T-Nut)
        translate([manifold_length/2 - 20, manifold_width/2, -1])
            cylinder(h = thickness + 2, d = 4.5);
        translate([manifold_length/2 + 20, manifold_width/2, -1])
            cylinder(h = thickness + 2, d = 4.5);
            
        // Ağırlık azaltma cepleri
        translate([30, 6, -1])
            cube([25, manifold_width - 12, thickness + 2]);
        translate([80, 6, -1])
            cube([25, manifold_width - 12, thickness + 2]);
    }
}

manifold_bracket();
