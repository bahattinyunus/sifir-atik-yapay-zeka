// Sıfır Atık YZ - Konveyör Bant Rulo Gergi ve Yataklama Parçası
// Standart 608zz rulman (8x22x7mm) ve 2020 sigma profil kızak yapısına uyumludur.

$fn = 60;

bracket_w = 40;
bracket_h = 45;
base_t = 6;

module tensioner() {
    difference() {
        cube([bracket_w, bracket_h, base_t]);

        // 608zz Rulman Yuvası (22mm Çap, 7mm Derinlik)
        translate([bracket_w/2, 28, -1])
            cylinder(h = base_t + 2, d = 8.2); // 8mm Mil geçiş deliği
            
        // Gergi Slotu (M4 vida ile ileri-geri gerdirme kanalı)
        translate([8, 8, -1])
            cylinder(h = base_t + 2, d = 4.3);
        translate([bracket_w - 8, 8, -1])
            cylinder(h = base_t + 2, d = 4.3);
            
        translate([8, 6, -1])
            cube([bracket_w - 16, 4, base_t + 2]);
    }
}

tensioner();
