# Tiles Removal Best Practices

This guide is for developers assigned specific JSPs to migrate away from Apache Tiles. It covers the practical steps to remove Tiles dependencies and achieve functional equivalence in your target replacement (Thymeleaf, plain JSP, or SiteMesh).

## Before You Start

- You have been assigned one or more JSP files to migrate
- You know which module owns those files
- Review the `tiles-inventory.csv` report for your module to understand the tiles definitions you depend on
- Understand the target replacement strategy (Thymeleaf, JSP includes, SiteMesh, etc.)

## Phase 1: Understanding Your Tiles Usage

### 1.1 Identify Tiles in Your JSP

Look for these Tiles-specific elements in your assigned JSP files:

**Taglib Declaration:**
```jsp
<%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="tiles" %>
```

**Tile Insertions:**
```jsp
<tiles:insertAttribute name="header" />
<tiles:insertAttribute name="content" />
<tiles:insertAttribute name="footer" />
<tiles:getAsString name="title" />
<tiles:insertDefinition name="myLayout" />
<tiles:importAttribute name="pageTitle" />
```

**Definition in XML (in tiles.xml or tiles-defs.xml):**
```xml
<definition name="myPage" extends="baseLayout">
  <put-attribute name="pageTitle" value="My Page" />
  <put-attribute name="content" value="/WEB-INF/views/my-content.jsp" />
</definition>
```

### 1.2 Map Your Dependencies

For each JSP you are migrating:

1. **Find the view name** used in your controller:
   ```java
   return "mymodule.myPage";  // or "myPage"
   ```

2. **Locate the definition** in `tiles.xml` or `tiles-defs.xml`:
   ```xml
   <definition name="mymodule.myPage" extends="base">
     <put-attribute name="title" value="My Title" />
     <put-attribute name="content" value="/WEB-INF/views/mymodule/content.jsp" />
   </definition>
   ```

3. **Follow the inheritance chain**:
   - Does it `extends="base"` or another definition?
   - What attributes does the parent provide?
   - Are there common attributes shared across multiple definitions?

4. **List all `<tiles:insertAttribute>` tags** in your JSP and what they expect:
   ```jsp
   <tiles:insertAttribute name="header" />    <!-- Expect from parent -->
   <tiles:insertAttribute name="content" />   <!-- Expect from parent -->
   <tiles:getAsString name="pageTitle" />     <!-- Expect as variable -->
   ```

### 1.3 Check for Shadowed Tiles

If multiple modules define the same tile name (e.g., multiple `header.jsp` files), note this in your migration plan. You may need to:
- Rename files to be module-specific
- Consolidate to a single shared version
- Reference the correct one explicitly in your new implementation

## Phase 2: Choose Your Migration Pattern

### Pattern 1: Thymeleaf + Layout Dialect (Recommended for Templating)

**When to use:** If moving to Spring Boot 3 or starting new templating.

**Steps:**
1. Create a `layout.html` template with `th:fragment` and `layout:fragment` placeholders
2. Rewrite your JSP as `*.html` using `layout:decorate="~{layout}"` 
3. Replace `<tiles:insertAttribute name="content" />` with `<div layout:fragment="content"></div>`

**Example:**
```html
<!-- layout.html -->
<!DOCTYPE html>
<html xmlns:layout="http://www.ultraq.net.nz/thymeleaf/layout">
<head>
    <title layout:fragment="title">Default</title>
</head>
<body>
    <header th:fragment="header">...</header>
    <main layout:fragment="content"></main>
    <footer th:fragment="footer">...</footer>
</body>
</html>

<!-- myPage.html -->
<!DOCTYPE html>
<html layout:decorate="~{layout}">
<head>
    <title layout:fragment="title">My Page Title</title>
</head>
<body>
    <div layout:fragment="content">
        <!-- Page-specific content -->
    </div>
</body>
</html>
```

### Pattern 2: JSP `<jsp:include>` / Tag Files (Minimal Refactoring)

**When to use:** Keeping JSP, simple layouts, least code changes.

**Steps:**
1. Extract layout JSPs (header, footer, nav) into separate files
2. Replace `<tiles:insertAttribute>` with `<jsp:include page="..." />`
3. Pass variables via request attributes or `<jsp:param>`

**Example:**
```jsp
<!-- layout.jsp -->
<%@ page language="java" %>
<html>
<head><title>${pageTitle}</title></head>
<body>
    <jsp:include page="/WEB-INF/views/header.jsp" />
    <main>
        <jsp:include page="${contentPage}" />
    </main>
    <jsp:include page="/WEB-INF/views/footer.jsp" />
</body>
</html>

<!-- myContent.jsp -->
<%@ page language="java" %>
<h1>${pageTitle}</h1>
<p>My content here</p>

<!-- controller -->
request.setAttribute("pageTitle", "My Page");
request.setAttribute("contentPage", "/WEB-INF/views/mymodule/content.jsp");
return "layout";
```

### Pattern 3: SiteMesh (Decorator Model)

**When to use:** If your layouts are mostly "wrap the page" without deep nesting.

**Steps:**
1. Configure SiteMesh decorators in `sitemesh.xml`
2. Create decorator JSPs that wrap content pages
3. Content pages remain mostly unchanged, SiteMesh intercepts and applies decorators

## Phase 3: Migration Steps

### Step 1: Create Your Target Files

**If using Thymeleaf:**
```bash
# Create layout template
touch src/main/resources/templates/layout.html

# Create page templates
touch src/main/resources/templates/mymodule/mypage.html
```

**If using JSP includes:**
```bash
# Create layout and component JSPs
touch src/main/webapp/WEB-INF/views/layout.jsp
touch src/main/webapp/WEB-INF/views/mymodule/content.jsp
```

### Step 2: Implement the Layout

Extract the effective layout from your Tiles definition:

```xml
<!-- Original tiles.xml definition -->
<definition name="mymodule.myPage" extends="baseLayout">
  <put-attribute name="title" value="My Page" />
  <put-attribute name="content" value="/WEB-INF/views/mymodule/content.jsp" />
</definition>

<!-- Original baseLayout definition -->
<definition name="baseLayout">
  <put-attribute name="header" value="/WEB-INF/views/common/header.jsp" />
  <put-attribute name="nav" value="/WEB-INF/views/common/nav.jsp" />
  <put-attribute name="footer" value="/WEB-INF/views/common/footer.jsp" />
  <put-attribute name="content" value="" />
</definition>
```

**Becomes (Thymeleaf):**
```html
<!-- layout.html -->
<!DOCTYPE html>
<html xmlns:layout="http://www.ultraq.net.nz/thymeleaf/layout">
<head>
    <title layout:fragment="title">Default Title</title>
</head>
<body>
    <div th:replace="~{common/header}"></div>
    <nav th:replace="~{common/nav}"></nav>
    <main layout:fragment="content"></main>
    <div th:replace="~{common/footer}"></div>
</body>
</html>

<!-- mypage.html -->
<!DOCTYPE html>
<html layout:decorate="~{layout}">
<head>
    <title layout:fragment="title">My Page</title>
</head>
<body>
    <div layout:fragment="content">
        <!-- Page-specific content from old /WEB-INF/views/mymodule/content.jsp -->
    </div>
</body>
</html>
```

**Becomes (JSP includes):**
```jsp
<!-- layout.jsp -->
<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<html>
<head><title>${pageTitle}</title></head>
<body>
    <jsp:include page="/WEB-INF/views/common/header.jsp" />
    <nav><jsp:include page="/WEB-INF/views/common/nav.jsp" /></nav>
    <main>
        <jsp:include page="${contentPage}" />
    </main>
    <jsp:include page="/WEB-INF/views/common/footer.jsp" />
</body>
</html>

<!-- mypage.jsp -->
<%@ page language="java" %>
<%
    request.setAttribute("pageTitle", "My Page");
    request.setAttribute("contentPage", "/WEB-INF/views/mymodule/content.jsp");
%>
<jsp:include page="/WEB-INF/views/layout.jsp" />
```

### Step 3: Update Your Controller

**Original (returning view name resolved by Tiles):**
```java
@Controller
public class MyController {
    @GetMapping("/mypage")
    public String myPage(Model model) {
        model.addAttribute("data", getData());
        return "mymodule.myPage";  // Tiles definition name
    }
}
```

**New (explicit view path for Thymeleaf):**
```java
@Controller
public class MyController {
    @GetMapping("/mypage")
    public String myPage(Model model) {
        model.addAttribute("data", getData());
        model.addAttribute("pageTitle", "My Page");  // Explicit for layout
        return "mymodule/mypage";  // Template path (Thymeleaf auto-prefixes)
    }
}
```

**New (explicit view path for JSP):**
```java
@Controller
public class MyController {
    @GetMapping("/mypage")
    public String myPage(Model model) {
        model.addAttribute("data", getData());
        model.addAttribute("pageTitle", "My Page");
        model.addAttribute("contentPage", "/WEB-INF/views/mymodule/content.jsp");
        return "mymodule/mypage";  // View name resolved by ViewResolver
    }
}
```

### Step 4: Remove Tiles JSP Code

**Original JSP (Tiles version):**
```jsp
<%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="tiles" %>

<tiles:insertAttribute name="header" />
<h1><tiles:getAsString name="pageTitle" /></h1>
<p>${data}</p>
<tiles:insertAttribute name="footer" />
```

**New JSP (plain includes):**
```jsp
<%@ page language="java" %>

<jsp:include page="/WEB-INF/views/common/header.jsp" />
<h1>${pageTitle}</h1>
<p>${data}</p>
<jsp:include page="/WEB-INF/views/common/footer.jsp" />
```

**New HTML (Thymeleaf):**
```html
<!DOCTYPE html>
<html xmlns:layout="http://www.ultraq.net.nz/thymeleaf/layout"
      layout:decorate="~{layout}">
<head>
    <title layout:fragment="title">[[${pageTitle}]]</title>
</head>
<body>
    <div layout:fragment="content">
        <h1>[[${pageTitle}]]</h1>
        <p th:text="${data}"></p>
    </div>
</body>
</html>
```

### Step 5: Handle Duplicated/Shadowed Components

If you found duplicated files in the shadowed-tiles report:

1. **Identify which one is actually used**: Check the XML definition order; first match wins
2. **Consolidate**: Keep the used version, delete the shadowed one, update references in other modules
3. **Rename if needed**: If both are legitimately different, rename them to be module-specific:
   - `/WEB-INF/views/common/header.jsp` → `/WEB-INF/views/common/header.jsp`
   - `/WEB-INF/views/special/header.jsp` → `/WEB-INF/views/special/special-header.jsp`

### Step 6: Replace ViewPreparer Logic

If your JSP uses `ViewPreparer` to populate model attributes:

**Original:**
```java
public class MyPreparer implements ViewPreparer {
    @Override
    public void execute(TilesRequestContext context, AttributeContext attributeContext) {
        context.getRequest().setAttribute("user", getCurrentUser());
        context.getRequest().setAttribute("menu", buildMenu());
    }
}
```

**New (with @ControllerAdvice):**
```java
@ControllerAdvice
public class GlobalModelAttributes {
    @ModelAttribute("user")
    public User getCurrentUser() {
        return userService.current();
    }
    
    @ModelAttribute("menu")
    public Menu buildMenu() {
        return menuService.build();
    }
}
```

Or use a `HandlerInterceptor`:
```java
@Component
public class ModelInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute("user", userService.current());
        request.setAttribute("menu", menuService.build());
        return true;
    }
}
```

## Phase 4: Testing

### Testing Checklist

- [ ] Page renders without Tiles errors or missing includes
- [ ] All CSS and JavaScript still load (check browser console)
- [ ] Layout structure (header, nav, footer) appears correctly
- [ ] Page-specific content displays
- [ ] Forms submit correctly
- [ ] Links and navigation work
- [ ] Error pages still work (404, 500, etc.)
- [ ] Session attributes and request data propagate to layout
- [ ] Mobile/responsive layout still works

### Manual Testing

```bash
# For each assigned JSP:
1. Start the app: mvn spring-boot:run
2. Navigate to the page in your browser
3. Inspect the rendered HTML in DevTools
4. Check Network tab for missing resources
5. Test form submissions
6. Test navigation to other pages
```

### Automated Testing

Add a smoke test to catch regressions:

```java
@SpringBootTest
@AutoConfigureMockMvc
public class TilesMigrationTest {
    @Autowired MockMvc mvc;
    
    @Test
    public void testMyPageRenders() throws Exception {
        mvc.perform(get("/mypage"))
           .andExpect(status().isOk())
           .andExpect(content().string(containsString("<h1>")))
           .andExpect(content().string(containsString("header")))
           .andExpect(content().string(containsString("footer")));
    }
}
```

## Phase 5: Final Cleanup

### Remove Tiles Configuration

1. **Delete definition files** your module owned:
   - `src/main/resources/tiles.xml`
   - `src/main/webapp/WEB-INF/tiles/tiles-defs.xml`

2. **Remove from `applicationContext.xml` or Spring Boot config**:
   ```xml
   <!-- Remove these -->
   <bean class="org.springframework.web.servlet.view.tiles3.TilesConfigurer">
       <property name="definitions" value="/WEB-INF/tiles/tiles-defs.xml" />
   </bean>
   <bean class="org.springframework.web.servlet.view.tiles3.TilesViewResolver" />
   ```

3. **Remove from `pom.xml`**:
   ```xml
   <!-- Remove -->
   <dependency>
       <groupId>org.apache.tiles</groupId>
       <artifactId>tiles-core</artifactId>
   </dependency>
   <dependency>
       <groupId>org.apache.tiles</groupId>
       <artifactId>tiles-jsp</artifactId>
   </dependency>
   <!-- etc. -->
   ```

4. **Remove taglib declarations** from all JSPs:
   ```jsp
   <!-- Remove this line -->
   <%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="tiles" %>
   ```

5. **Grep for lingering references**:
   ```bash
   grep -r "tiles" src/main/webapp/WEB-INF/ --include="*.xml" --include="*.jsp"
   grep -r "TilesConfigurer\|TilesViewResolver\|ViewPreparer" src/ --include="*.java"
   grep -r "org.apache.tiles" pom.xml
   ```

### Update Web Descriptor (if applicable)

In `web.xml`, remove Tiles servlet definitions if present:
```xml
<!-- Remove -->
<servlet>
    <servlet-name>tilesDispatcher</servlet-name>
    <servlet-class>org.springframework.web.servlet.DispatcherServlet</servlet-class>
</servlet>
```

## Common Pitfalls

### Pitfall 1: Forgetting Variable Passing

**Problem:** Layout references variables that aren't in model.
```jsp
<!-- layout.jsp -->
<title>${pageTitle}</title>  <!-- But pageTitle never set -->
```

**Solution:** Ensure all variables used in layout are set in controller or via @ModelAttribute.

### Pitfall 2: Nested Includes Not Working

**Problem:** JSP include paths are relative to current JSP, not web root.
```jsp
<!-- /WEB-INF/views/mymodule/page.jsp -->
<jsp:include page="header.jsp" />  <!-- Wrong! Looks for /WEB-INF/views/mymodule/header.jsp -->
```

**Solution:** Use absolute paths from web root.
```jsp
<jsp:include page="/WEB-INF/views/common/header.jsp" />
```

### Pitfall 3: Missing RequestDispatcher Forward

**Problem:** Some framework code expects Tiles to handle the view render.
```java
// Old code expecting Tiles to render
request.getRequestDispatcher("myTilesDefinition").forward(request, response);
```

**Solution:** Return view name from controller or use explicit forward:
```java
// Use Spring's view name return instead
return "mymodule/mypage";

// Or explicit forward to the layout
request.getRequestDispatcher("/WEB-INF/views/layout.jsp").forward(request, response);
```

### Pitfall 4: CSS/JS Missing After Migration

**Problem:** Relative paths in CSS/JS break when template moves.
```jsp
<!-- Old: /WEB-INF/views/mymodule/page.jsp -->
<link rel="stylesheet" href="../../css/style.css">
```

**Solution:** Use context-relative paths or Spring url tag.
```jsp
<!-- JSP -->
<link rel="stylesheet" href="${pageContext.request.contextPath}/css/style.css">

<!-- Thymeleaf -->
<link rel="stylesheet" th:href="@{/css/style.css}">
```

### Pitfall 5: Shadowed Tiles Resolved to Wrong File

**Problem:** Multiple modules define the same tile name; definition order matters.
```xml
<!-- module-a/tiles.xml -->
<definition name="header" value="/WEB-INF/views/a/header.jsp" />

<!-- module-b/tiles.xml -->
<definition name="header" value="/WEB-INF/views/b/header.jsp" />
<!-- First one loaded wins -->
```

**Solution:** Use module-scoped names.
```xml
<!-- module-a/tiles.xml -->
<definition name="moduleA.header" value="/WEB-INF/views/a/header.jsp" />

<!-- module-b/tiles.xml -->
<definition name="moduleB.header" value="/WEB-INF/views/b/header.jsp" />
```

## Checklist for Your Task

- [ ] Read `tiles-inventory.csv` and understand your assignments
- [ ] Identify all Tiles usage in your assigned JSPs
- [ ] Map the dependency tree for each assigned view
- [ ] Choose and plan your migration pattern (Thymeleaf / JSP / SiteMesh)
- [ ] Create target layout/template files
- [ ] Migrate page-specific content
- [ ] Update controller view names and model attributes
- [ ] Remove Tiles taglib and insertAttribute calls
- [ ] Handle any shadowed or duplicate components
- [ ] Test all pages render correctly
- [ ] Remove Tiles configuration from XML/properties
- [ ] Remove Tiles dependencies from pom.xml
- [ ] Run final grep to catch any stragglers
- [ ] Verify all tests pass (unit + integration + smoke)

## Questions or Blocked?

- Check the `tiles-inventory.csv` columns: `effective_template` shows the fully flattened definition, `num_attrs` shows attribute count
- See `tiles-config.md` for a checklist of every Tiles reference to grep for
- Review `tiles-assignments.md` to see if your definitions depend on shared ones (Phase 0 blockers)
- Ask your tech lead if a definition is unclear or has complex inheritance
