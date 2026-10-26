-- Apply Dan's "00 Curated" view (columns, Songs view, no artwork) to Music playlists.
-- Usage: osascript apply_playlist_view.applescript [playlist name | --folders]   (no arg = every playlist and folder)
property onCols : {"Album", "Artist", "Cloud Download", "Genre", "Time", "Comments", "Favourite", "Date Added", "Plays"}

on panelReady()
	tell application "System Events" to tell process "Music"
		if not (exists window "View Options") then return false
		return ((count of scroll areas of window "View Options") > 0)
	end tell
end panelReady

on ensurePanel()
	tell application "System Events" to tell process "Music"
		set vm to menu 1 of menu bar item "View" of menu bar 1
		if not (exists window "View Options") then
			click menu bar item "View" of menu bar 1
			delay 0.4
			try
				click menu item "Show View Options" of menu 1 of menu bar item "View" of menu bar 1
			end try
			delay 0.3
			if not (exists window "View Options") then key code 53
		end if
	end tell
	repeat 15 times
		if my panelReady() then return true
		delay 0.3
	end repeat
	return false
end ensurePanel

on expandAll()
	tell application "System Events" to tell process "Music"
		set sa to scroll area 1 of window "View Options"
		set tris to (UI elements of sa whose role is "AXDisclosureTriangle")
		set nt to count of tris
		repeat with i from 1 to nt
			set nBefore to count of (checkboxes of sa)
			click item i of (UI elements of sa whose role is "AXDisclosureTriangle")
			delay 0.3
			if (count of (checkboxes of sa)) < nBefore then
				click item i of (UI elements of sa whose role is "AXDisclosureTriangle")
				delay 0.3
			end if
		end repeat
	end tell
end expandAll

on applyOne(pid)
	tell application "System Events" to tell process "Music"
		set vm0 to menu 1 of menu bar item "View" of menu bar 1
		if exists menu item "Hide View Options" of vm0 then
			click menu item "Hide View Options" of vm0
			delay 0.4
		end if
		if exists window "View Options" then
			try
				click (first button of window "View Options" whose subrole is "AXCloseButton")
				delay 0.4
			end try
		end if
	end tell
	tell application "Music"
		set p to (first playlist whose persistent ID is pid)
		if special kind of p is not none and special kind of p is not folder then return (name of p) & " | SKIP special playlist"
		set pn to name of p
		reopen
		activate
		reveal p
	end tell
	delay 0.8
	tell application "System Events" to tell process "Music"
		if not (exists window "Music") then error "Music window not reachable (other desktop/full screen?)"
		perform action "AXRaise" of window "Music"
	end tell
	delay 0.3
	tell application "System Events" to tell process "Music"
		set vm to menu 1 of menu bar item "View" of menu bar 1
		if exists menu item "as Songs" of vm then
			if enabled of menu item "as Songs" of vm then click menu item "as Songs" of vm
		else
			error "no 'as Songs' in View menu"
		end if
		delay 0.5
	end tell
	if not my ensurePanel() then return pn & " | SKIP no view options"
	tell application "System Events" to tell process "Music"
		set sa to scroll area 1 of window "View Options"
		set t to ""
		repeat 15 times
			try
				set t to value of static text 1 of sa
			end try
			if t is pn then exit repeat
			delay 0.3
		end repeat
		if t is not pn then return pn & " | SKIP panel shows " & t
		if (count of (checkboxes of sa)) < 38 then my expandAll()
		set changed to {}
		repeat with cb in (checkboxes of sa)
			set n to name of cb
			set want to 0
			if onCols contains n then set want to 1
			if (value of cb) is not want then
				click cb
				delay 0.1
				set end of changed to n
			end if
		end repeat
		try
			set art to checkbox "Show Artwork" of window "View Options"
			if value of art is 1 then
				click art
				set end of changed to "Show Artwork"
			end if
		end try
		set bad to {}
		repeat with cb in (checkboxes of sa)
			set n to name of cb
			set want to 0
			if onCols contains n then set want to 1
			if (value of cb) is not want then set end of bad to n
		end repeat
		set AppleScript's text item delimiters to ","
		return pn & " | changed=" & (changed as text) & " | bad=" & (bad as text) & " | n=" & (count of (checkboxes of sa))
	end tell
end applyOne

on run argv
	tell application "Music"
		if (count of argv) > 0 and (item 1 of argv) is "--folders" then
			set pids to persistent ID of every folder playlist
		else if (count of argv) > 0 then
			set pids to {persistent ID of (first playlist whose name is (item 1 of argv))}
		else
			set pids to (persistent ID of every user playlist) & (persistent ID of every folder playlist)
		end if
	end tell
	set out to ""
	repeat with pid in pids
		set r to ""
		repeat 2 times
			try
				set r to my applyOne(pid as text)
			on error e
				set r to (pid as text) & " | ERROR " & e
			end try
			if r does not contain "SKIP" and r does not contain "ERROR" then exit repeat
			delay 1
		end repeat
		do shell script "echo " & quoted form of r & " >> /tmp/applyview.log"
		set out to out & r & linefeed
	end repeat
	return out
end run
