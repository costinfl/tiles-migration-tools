package com.example.shared;

import java.util.Arrays;
import java.util.List;

public final class MenuService {
    private MenuService() { }
    public static List<String> items() {
        return Arrays.asList("Vets", "Visits", "Owners");
    }
}
