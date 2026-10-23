// Sıfır Atık YZ - Ayarlanabilir Kamera ve IR Sensör Taşıyıcı Braketi
// Konveyör bandın üzerine tepeden bakacak şekilde 2020 sigma profile monte edilir.
// WebCam veya PiCamera V2 / V3 ile uyumludur.

$fn = 50;

mount_width = 50;
mount_height = 40;
thickness = 3.5;

module camera_mount() {
    difference() {
        // Ana gövde
        cube([mount_width, mount_height, thickness]);

        // PiCamera Standart Montaj Delikleri (21mm x 12.5mm aralık, M2 cıvata)
        translate([mount_width/2 - 10.5, mount_height/2 - 6.25, -1])
            cylinder(h = thickness + 2, d = 2.4);
        translate([mount_width/2 + 10.5, mount_height/2 - 6.25, -1])
            cylinder(h = thickness + 2, d = 2.4);
        translate([mount_width/2 - 10.5, mount_height/2 + 6.25, -1])
            cylinder(h = thickness + 2, d = 2.4);
        translate([mount_width/2 + 10.5, mount_height/2 + 6.25, -1])
            cylinder(h = thickness + 2, d = 2.4);

        // Kamera lensi geçiş penceresi
        translate([mount_width/2, mount_height/2, -1])
            cylinder(h = thickness + 2, d = 16);

        // Yan profil montaj kanalları (M4 T-Nut için slotlar)
        translate([6, 8, -1])
            cylinder(h = thickness + 2, d = 4.3);
        translate([mount_width - 6, 8, -1])
            cylinder(h = thickness + 2, d = 4.3);
    }
}

camera_mount();
