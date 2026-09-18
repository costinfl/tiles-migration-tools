package com.example.vets;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.servlet.ModelAndView;

@Controller
public class VetController {

    private static final String LIST_VIEW = "vets.list";

    @GetMapping("/vets")
    public ModelAndView list() {
        ModelAndView mav = new ModelAndView(LIST_VIEW);
        mav.addObject("vets", VetRepository.all());
        return mav;
    }

    @GetMapping("/vets/{id}")
    public ModelAndView detail(@PathVariable String id) {
        return new ModelAndView("vets.surgeon.detail");
    }

    @GetMapping("/vets/legacy")
    public String legacy() {
        return "vets.legacy";
    }
}
