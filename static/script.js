(function(){
    'use strict';

    var sidebar = document.getElementById('sidebar');
    var menuToggle = document.getElementById('menu-toggle');
    var panel = document.querySelector('.commentary-container');
    var sefariaBox = document.getElementById('sefaria-box');
    var sefariaLink = document.getElementById('sefaria-link');
    var chapterIndicator = document.getElementById('chapter-indicator');
    var content = document.querySelector('.content');

    var BOOK_BASE_URL = {
        'Genesis':'https://www.sefaria.org/Genesis',
        'Exodus':'https://www.sefaria.org/Exodus',
        'Leviticus':'https://www.sefaria.org/Leviticus',
        'Numbers':'https://www.sefaria.org/Numbers',
        'Deuteronomy':'https://www.sefaria.org/Deuteronomy'
    };

    function isMobile(){ return window.innerWidth <= 980; }

    /* ---------------- sidebar: overlay + toggle ---------------- */
    var overlay = document.createElement('div');
    overlay.id = 'sidebar-overlay';
    document.body.appendChild(overlay);

    function openSidebar(){
        sidebar.classList.add('open');
        overlay.classList.add('open');
    }
    function closeSidebar(){
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
    }
    if(menuToggle){
        menuToggle.addEventListener('click', function(){
            sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
        });
    }
    overlay.addEventListener('click', closeSidebar);

    /* ---------------- sidebar: accordion + active link ---------------- */
    (function setupSidebarAccordion(){
        if(!sidebar) return;
        var topList = sidebar.querySelector(':scope > ul');
        if(!topList) return;

        var currentFile = decodeURIComponent(location.pathname.split('/').pop() || '');

        Array.prototype.forEach.call(topList.children, function(li){
            var nestedUl = li.querySelector(':scope > ul');
            if(!nestedUl) return;

            var labelText = li.childNodes[0] && li.childNodes[0].nodeType === 3
                ? li.childNodes[0].textContent.trim()
                : (li.firstChild ? li.firstChild.textContent : '');

            var toggle = document.createElement('span');
            toggle.className = 'book-toggle';
            toggle.textContent = labelText;

            if(li.childNodes[0] && li.childNodes[0].nodeType === 3){
                li.removeChild(li.childNodes[0]);
            }
            li.insertBefore(toggle, nestedUl);

            var containsActive = false;
            Array.prototype.forEach.call(nestedUl.querySelectorAll('a'), function(a){
                var href = decodeURIComponent(a.getAttribute('href') || '');
                if(href && currentFile && href === currentFile){
                    a.classList.add('active');
                    containsActive = true;
                }
            });

            if(containsActive) li.classList.add('open');

            toggle.addEventListener('click', function(){
                li.classList.toggle('open');
            });
        });
    })();

    /* ---------------- sefaria panel open/close ---------------- */
    function openPanel(){
        if(panel) panel.classList.add('open');
    }
    function closePanel(){
        if(panel) panel.classList.remove('open');
    }

    if(panel){
        var closeHandle = document.createElement('div');
        closeHandle.className = 'panel-close';
        closeHandle.setAttribute('aria-label', 'Bezárás');
        panel.insertBefore(closeHandle, panel.firstChild);
        closeHandle.addEventListener('click', closePanel);

        var emptyState = document.createElement('div');
        emptyState.className = 'panel-empty';
        emptyState.innerHTML = '<div class="seal">א</div>Kattints egy pászukra,<br>és megjelenik itt a Sefaria-link.';
        panel.appendChild(emptyState);
    }

    document.addEventListener('keydown', function(e){
        if(e.key === 'Escape'){
            closeSidebar();
            closePanel();
        }
    });

    /* ---------------- verse interaction ---------------- */
    function clearActiveVerse(){
        Array.prototype.forEach.call(document.querySelectorAll('.active-verse'), function(el){
            el.classList.remove('active-verse');
        });
        Array.prototype.forEach.call(document.querySelectorAll('tr.active-row'), function(el){
            el.classList.remove('active-row');
        });
    }

    window.showSefariaLink = function(chapter, verse, book){
        clearActiveVerse();

        var verseId = 'ch' + chapter + '-vrs' + verse;
        var markers = document.querySelectorAll('[id="' + verseId + '"], .' + 'vrs-' + verseId);
        Array.prototype.forEach.call(markers, function(m){
            m.classList.add('active-verse');
            var row = m.closest('tr');
            if(row) row.classList.add('active-row');
        });

        var baseUrl = BOOK_BASE_URL[book] || ('https://www.sefaria.org/' + book);
        var url = baseUrl + '.' + chapter + '.' + verse;

        if(sefariaLink) sefariaLink.href = url;

        if(sefariaBox){
            var label = sefariaBox.querySelector('.vrs-label');
            if(!label){
                label = document.createElement('p');
                label.className = 'vrs-label';
                sefariaBox.insertBefore(label, sefariaBox.firstChild);
            }
            label.textContent = book + ' ' + chapter + ':' + verse;
            sefariaBox.style.display = 'block';
        }

        if(isMobile()){
            openPanel();
        }
    };

    /* wrap hungarian verse numbers ("10.", "11.") so they are clickable too,
       matched positionally against the hebrew verse anchors in the same row */
    (function enhanceHungarianVerseNumbers(){
        var rows = document.querySelectorAll('.bilingual-table tr');
        Array.prototype.forEach.call(rows, function(tr){
            var heCell = tr.querySelector('td.he');
            var huCell = tr.querySelector('td.hu');
            if(!heCell || !huCell) return;

            var anchors = heCell.querySelectorAll('p > a[onclick]');
            if(!anchors.length) return;

            var verseInfo = [];
            Array.prototype.forEach.call(anchors, function(a){
                var m = /showSefariaLink\((\d+),\s*(\d+),\s*'([^']+)'\)/.exec(a.getAttribute('onclick') || '');
                if(m){
                    verseInfo.push({ chapter:m[1], verse:m[2], book:m[3], anchorId:a.id });
                }
            });
            if(!verseInfo.length) return;

            var huP = huCell.querySelector('p');
            if(!huP) return;

            var boldNums = huP.querySelectorAll('strong');
            var idx = 0;
            Array.prototype.forEach.call(boldNums, function(strong){
                var text = strong.textContent.trim();
                if(!/^\d+\.$/.test(text)) return;
                if(idx >= verseInfo.length) return;

                var info = verseInfo[idx];
                strong.classList.add('vrs-num');
                strong.classList.add('vrs-ch' + info.chapter + '-vrs' + info.verse);
                strong.setAttribute('role', 'button');
                strong.setAttribute('tabindex', '0');
                strong.addEventListener('click', function(){
                    window.showSefariaLink(info.chapter, info.verse, info.book);
                });
                strong.addEventListener('keydown', function(e){
                    if(e.key === 'Enter' || e.key === ' '){
                        e.preventDefault();
                        window.showSefariaLink(info.chapter, info.verse, info.book);
                    }
                });
                idx++;
            });
        });
    })();

    /* ---------------- chapter indicator on scroll ---------------- */
    (function setupChapterIndicator(){
        var headings = document.querySelectorAll('.bilingual-table td.hu h1');
        if(!headings.length || !chapterIndicator) return;

        var scroller = content || window;

        function currentChapterLabel(){
            var scrollTop = window.scrollY || document.documentElement.scrollTop;
            var best = null;
            Array.prototype.forEach.call(headings, function(h){
                var top = h.getBoundingClientRect().top + scrollTop;
                if(top - 120 <= scrollTop) best = h;
            });
            return best;
        }

        function update(){
            var h = currentChapterLabel();
            if(h){
                chapterIndicator.textContent = h.textContent.trim();
                chapterIndicator.classList.add('visible');
            } else {
                chapterIndicator.classList.remove('visible');
            }
        }

        window.addEventListener('scroll', update, { passive:true });
        window.addEventListener('resize', update);
        update();
    })();

})();
