function toggleMenu(id){

let menu = document.getElementById(id);

if(menu.style.display === "block"){
    menu.style.display = "none";
}else{
    menu.style.display = "block";
}

}

(function initFlyoutMenus(){
    const flyoutItems = Array.from(document.querySelectorAll('.menu-item.has-flyout'));
    if (!flyoutItems.length) return;

    const closeDelayMap = new WeakMap();

    function closeSublevels(parent){
        parent.querySelectorAll('.has-sublevel.open').forEach((node) => node.classList.remove('open'));
    }

    function closeAllFlyouts(except){
        flyoutItems.forEach((item) => {
            if (except && item === except) return;
            item.classList.remove('open');
            const trigger = item.querySelector('[data-flyout-trigger]');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
            closeSublevels(item);
        });
    }

    function openFlyout(item){
        closeAllFlyouts(item);
        item.classList.add('open');
        const trigger = item.querySelector('[data-flyout-trigger]');
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
    }

    function scheduleClose(item, ms = 220){
        const prev = closeDelayMap.get(item);
        if (prev) clearTimeout(prev);
        const t = setTimeout(() => {
            item.classList.remove('open');
            const trigger = item.querySelector('[data-flyout-trigger]');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
            closeSublevels(item);
        }, ms);
        closeDelayMap.set(item, t);
    }

    function clearClose(item){
        const prev = closeDelayMap.get(item);
        if (prev) clearTimeout(prev);
    }

    flyoutItems.forEach((item) => {
        const trigger = item.querySelector('[data-flyout-trigger]');
        const panel = item.querySelector('.submenu-flyout');
        if (!trigger) return;

        trigger.addEventListener('click', (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            const isOpen = item.classList.contains('open');
            if (isOpen) {
                item.classList.remove('open');
                trigger.setAttribute('aria-expanded', 'false');
                closeSublevels(item);
            } else {
                openFlyout(item);
            }
        });

        item.addEventListener('mouseenter', () => {
            clearClose(item);
            openFlyout(item);
        });
        item.addEventListener('mouseleave', () => {
            scheduleClose(item);
        });

        if (panel) {
            panel.addEventListener('mouseenter', () => {
                clearClose(item);
                openFlyout(item);
            });
            panel.addEventListener('mouseleave', () => {
                scheduleClose(item);
            });
        }

        item.querySelectorAll('.has-sublevel').forEach((subItem) => {
            const subTrigger = subItem.querySelector('.submenu-nested-trigger');
            if (!subTrigger) return;

            subTrigger.addEventListener('click', (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
                subItem.classList.toggle('open');
            });

            subItem.addEventListener('mouseenter', () => subItem.classList.add('open'));
            subItem.addEventListener('mouseleave', () => subItem.classList.remove('open'));
        });
    });

    document.addEventListener('click', (ev) => {
        const inside = ev.target && ev.target.closest('.menu-item.has-flyout');
        if (!inside) closeAllFlyouts();
    });

    document.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape') closeAllFlyouts();
    });
})();