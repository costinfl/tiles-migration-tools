package com.example.shared;

import org.apache.tiles.AttributeContext;
import org.apache.tiles.preparer.ViewPreparer;
import org.apache.tiles.request.Request;

public class MenuPreparer implements ViewPreparer {
    @Override
    public void execute(Request request, AttributeContext attributeContext) {
        request.getContext("request").put("menuItems", MenuService.items());
    }
}
