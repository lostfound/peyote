SUBDIRS = icons 

desktopdir = ${DESKDIR}
desktop_DATA = peyote.desktop mescaline.desktop

skinsdir = ${datarootdir}/peyote/skins
skins_DATA = \
skins/mc_traditional.peyote.skin \
skins/urxvt-black-n-green.peyote.skin \
skins/urxvt-dark_pastel.peyote.skin \
skins/transparent.peyote.skin \
skins/urxvt-solarized.peyote.skin


iconsdir = /usr/share
nobase_dist_icons_DATA = \
icons/hicolor/16x16/apps/peyote.png \
icons/hicolor/24x24/apps/peyote.png \
icons/hicolor/32x32/apps/peyote.png \
icons/hicolor/48x48/apps/peyote.png \
icons/hicolor/64x64/apps/peyote.png 

install-data-hook: update_menus
uninstall-hook: update_menus

update_menus:
	if "$(UPDATE_MENUS)" != ":"; then \
		$(UPDATE_MENUS); \
	elif "$(UPDATE_DESKTOP_DATABASE)" != ":"; then \
		$(UPDATE_DESKTOP_DATABASE) $(DESKDIR); \
	fi
	
