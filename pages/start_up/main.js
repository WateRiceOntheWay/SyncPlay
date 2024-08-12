function autoResize(caller) {
    // 获取iframe元素:
    const iframeEle = caller;
    // 创建一个ResizeObserver:
    const resizeRo = new ResizeObserver((entries) => {
        let entry = entries[0];
        let height = entry.contentRect.height;
        console.log(entry)
        iframeEle.style.height =  `${parseInt(height)+50}px`;
    });
    // 开始监控iframe的body元素:
    resizeRo.observe(iframeEle.contentWindow.document.body);
}