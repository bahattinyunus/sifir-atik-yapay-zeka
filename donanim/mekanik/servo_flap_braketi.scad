// Sıfır Atık YZ - MG996R Servo ve Mekanik Ayrıştırıcı Flap Montaj Braketi
// 2020 Alüminyum Sigma Profile ve MG996R metal dişli servoya tam uyumludur.
// OpenSCAD ile düzenlenebilir veya STL formatına ihraç edilip 3D yazıcıdan basılabilir.

$fn = 60;

// Ana Parametreler (mm)
bracket_width = 45;
bracket_length = 65;
bracket_thickness = 4;
profile_slot_distance = 20;

module base_plate() {
    difference() {
        cube([bracket_length, bracket_width, bracket_thickness], center = false);
        
        // 2020 Sigma Profil Montaj Delikleri (M4 Cıvata)
        translate([10, bracket_width/2 - profile_slot_distance/2, -1])
            cylinder(h = bracket_thickness + 2, d = 4.3);
        translate([10, bracket_width/2 + profile_slot_distance/2, -1])
            cylinder(h = bracket_thickness + 2, d = 4.3);
            
        // MG996R Servo Gövde Yuvası (40.5mm x 20mm)
        translate([28, bracket_width/2 - 10, -1])
            cube([40.5, 20.2, bracket_thickness + 2]);
            
        // Servo Sabitleme Kulak Delikleri (M3 Cıvata)
        translate([25, bracket_width/2 - 5, -1])
            cylinder(h = bracket_thickness + 2, d = 3.2);
        translate([25, bracket_width/2 + 5, -1])
            cylinder(h = bracket_thickness + 2, d = 3.2);
        translate([28 + 40.5 + 3, bracket_width/2 - 5, -1])
            cylinder(h = bracket_thickness + 2, d = 3.2);
        translate([28 + 40.5 + 3, bracket_width/2 + 5, -1])
            cylinder(h = bracket_thickness + 2, d = 3.2);
    }
}

module side_support() {
    difference() {
        cube([bracket_length, 4, 18]);
        translate([bracket_length - 15, -1, 10])
            rotate([0, 45, 0])
                cube([25, 6, 25]);
    }
}

// Montaj
union() {
    base_plate();
    translate([0, 0, 0]) side_support();
    translate([0, bracket_width - 4, 0]) side_support();
}
