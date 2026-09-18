package com.example.vets;

import java.util.Arrays;
import java.util.List;

public final class VetRepository {
    private VetRepository() { }
    public static List<String> all() {
        return Arrays.asList("Dr. Hibbert", "Dr. Nick");
    }
}
