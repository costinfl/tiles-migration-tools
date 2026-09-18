package com.example.visits;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.ModelAndView;

@Controller
public class VisitController {

    @GetMapping("/visits")
    public ModelAndView calendar(@RequestParam(required = false) String view) {
        ModelAndView mav = new ModelAndView("visits.calendar");
        String chosen = resolveView(view);
        mav.setViewName(chosen);
        return mav;
    }

    @GetMapping("/visits/detail")
    public ModelAndView detail() {
        return new ModelAndView("visits.detail");
    }

    @GetMapping("/visits/export")
    public ModelAndView export() {
        return new ModelAndView("visits.export.pdf");
    }

    private String resolveView(String view) {
        return view == null ? "visits.calendar" : "visits." + view;
    }
}
