var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?2d987a7a5924beded73be64dd7fe4b9b";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
})();

$(function () {
    const $div = $("<div></div>");
    $div.css({
      "border-top-left-radius": "34px",
      "border-bottom-left-radius": "34px",
      background: "linear-gradient(140.91deg, #FF87B7 12.61%, #EC4C8C 76.89%)",
      height: "34px",
      width: "60px",
      margin: "1px",
      display: "flex",
      "align-items": "center",
      position: "fixed",
      right: "0px",
      top: `50px`,
      cursor: "pointer",
    });
    $div.html(
      "<span style='color:white;font-size:15px;margin-left:10px'>换通道</span>"
    );
    $("body").append($div);
    $div.click(function () {
      window.location.href = "/list";
    });

    const $cz= $("<div></div>"); 
    $cz.css({
      "border-top-left-radius": "34px",
      "border-bottom-left-radius": "34px",
      background: "linear-gradient(103.91deg, #9B51E0 21.01%, rgba(48, 129, 237, 0.8) 100%)",
      height: "34px",
      width: "80px",
      margin: "1px",
      display: "flex",
      "align-items": "center",
      position: "fixed",
      right: "0px",
      top: `90px`,
      cursor: "pointer",
    });

    $cz.html( "<span style='color:white;font-size:15px;margin-left:10px'>充值续费</span>" );
    $("body").append($cz);
    $cz.click(function () {
      window.location.href = "/chongzhi";
    });
    
  });

  