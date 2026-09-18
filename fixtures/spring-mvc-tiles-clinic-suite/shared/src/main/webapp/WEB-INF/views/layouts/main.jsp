<%@ taglib uri="http://tiles.apache.org/tags-tiles" prefix="tiles" %>
<html>
<head><title><tiles:getAsString name="title" /></title></head>
<body>
  <tiles:insertAttribute name="header" />
  <tiles:insertAttribute name="nav" ignore="true" />
  <tiles:insertAttribute name="body" />
  <tiles:insertAttribute name="footer" />
</body>
</html>
