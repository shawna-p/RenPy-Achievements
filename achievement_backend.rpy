################################################################################
##
## Achievements for Ren'Py by Feniks (feniksdev.itch.io / feniksdev.com)
##
################################################################################
## This file contains code for an achievement system in Ren'Py. It is designed
## as a wrapper to the built-in achievement system, so it hooks into the
## Steam backend as well if you set up your achievement IDs the same as in
## the Steam backend.
##
## If you use this code in your projects, credit me as Feniks @ feniksdev.com
##
## If you'd like to see how to use this tool, check the other file,
## achievements.rpy!
##
## Leave a comment on the tool page on itch.io or an issue on the GitHub
## if you run into any issues.
################################################################################
init -50 python:
    import datetime, time
    from re import sub as re_sub

    TAG_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
    def get_random_screen_tag(k=4):
        """Generate a random k-letter word out of alphabet letters."""

        # Shuffle the list and pop k items from the front
        alphabet = list(store.TAG_ALPHABET)
        renpy.random.shuffle(alphabet)
        ## Add the time onto the end so there are no duplicates
        return ''.join(alphabet[:k] + [str(time.time())])


    class Achievement():
        """
        A class with information on in-game achievements which can be extended
        to use with other systems (e.g. Steam achievements).

        Attributes:
        -----------
        name : string
            The human-readable name of this achievement. May have spaces,
            apostrophes, dashes, etc.
        id : string
            The code-friendly name of this achievement (which can be used for
            things like the Steam backend). Should only include letters,
            numbers, and underscores. If not provided, name will be sanitized
            for this purpose.
        description : string
            A longer description for this achievement. Optional.
        unlocked_image : Displayable
            A displayable to use when this achievement is unlocked.
        locked_image : Displayable
            A displayable to use when this achievement is locked. If not
            provided, requires an image named "locked_achievement" to be
            declared somewhere.
        stat_max : int
            If provided, an integer corresponding to the maximum progress of
            an achievement, if the achievement can be partially completed
            (e.g. your game has 24 chapters and you want this to tick up
            after every chapter, thus, stat_max is 24). The achievement is
            unlocked when it reaches this value.
        stat_progress : int
            The current progress for the stat.
        stat_modulo : int
            The formula (stat_progress % stat_modulo) is applied whenever
            achievement progress is updated. If the result is 0, the
            progress is shown to the user. By default this is 0 so all updates
            to stat_progress are shown. Useful if, for the supposed 24-chapter
            game progress stat, you only wanted to show updates every time the
            player got through a quarter of the chapters. In this case,
            stat_modulo would be 6 (24//4).
        hidden : bool
            True if this achievement's description and name should be hidden
            from the player.
        hide_description : bool
            True if this achievement's description should be hidden from the
            player. Can be set separately from hidden, e.g. with hidden=True
            and hide_description=False, the player will see the name but not
            the description.
        timestamp : Datetime
            The time this achievement was unlocked at.
        """
        ## A list of all the achievements that exist in this game,
        ## to loop over in the achievements screen.
        all_achievements = [ ]
        achievement_dict = dict()
        def __init__(self, name, id=None, description=None, unlocked_image=None,
                locked_image=None, stat_max=None, stat_modulo=0, hidden=False,
                stat_update_percent=1, hide_description=None):

            self._name = name
            # Try to sanitize the name for an id, if possible
            self.id = id or re_sub(r'\W+', '', name)

            self._description = description or ""
            self.unlocked_image = unlocked_image or None
            self.locked_image = locked_image or "locked_achievement"

            self.stat_max = stat_max
            self.stat_modulo = stat_modulo
            if stat_update_percent != 1 and stat_modulo != 0:
                raise Exception("Achievement {} has both stat_update_percent and stat_modulo set. Please only set one.".format(self.name))
            ## Figure out the modulo based on the percent
            if stat_update_percent > 1:
                ## Basically, if stat_max % stat_modulo == 0, then it updates.
                ## So if it updates every 10%, then stat_max / stat_modulo = 10
                self.stat_modulo = int(stat_max * (stat_update_percent / 100.0))

            self.hidden = hidden
            if hide_description is None:
                self.hide_description = hidden
            else:
                self.hide_description = hide_description

            # Add to list of all achievements
            self.all_achievements.append(self)
            # Add to the dictionary for a quick lookup
            self.achievement_dict[self.id] = self

            # Register with backends
            achievement.register(self.id, stat_max=stat_max, stat_modulo=stat_modulo)

        def get_timestamp(self, format="%b %d, %Y @ %I:%M %p"):
            """
            Return the timestamp when this achievement was granted,
            using the provided string format.
            """
            if self.has():
                return datetime.datetime.fromtimestamp(
                    self._timestamp).strftime(format)
            else:
                return ""

        @property
        def _timestamp(self):
            if store.persistent.achievement_timestamp is not None:
                return store.persistent.achievement_timestamp.get(self.id, None)
            else:
                return None

        @property
        def timestamp(self):
            """Return the timestamp when this achievement was granted."""
            if self.has():
                try:
                    ts = datetime.datetime.fromtimestamp(self._timestamp)
                except TypeError:
                    if config.developer:
                        print("WARNING: Could not find timestamp for achievement with ID {}".format(self.id))
                    return ""
                return __("Unlocked ") + ts.strftime(__(
                    "%b %d, %Y @ %I:%M %p{#achievement_timestamp}"))
            else:
                return ""

        @_timestamp.setter
        def _timestamp(self, value):
            """Set the timestamp for this achievement."""
            if store.persistent.achievement_timestamp is not None:
                store.persistent.achievement_timestamp[self.id] = value

        @property
        def idle_img(self):
            """Return the idle image based on its locked status."""
            if self.has():
                return self.unlocked_image
            else:
                return self.locked_image

        @property
        def name(self):
            """
            Returns the name of the achievement based on whether it's
            hidden or not.
            """
            if self.hidden and not self.has():
                return _("???{#hidden_achievement_name}")
            else:
                return self._name

        @property
        def description(self):
            """
            Returns the description of the achievement based on whether it's
            hidden or not.
            """
            if self.hide_description and not self.has():
                if self.hide_description is True:
                    return _("???{#hidden_achievement_description}")
                else:
                    return self.hide_description
            else:
                return self._description

        @property
        def stat_progress(self):
            """Return this achievement's progress stat."""
            return self.get_progress()

        def add_progress(self, amount=1):
            """
            Increment the progress towards this achievement by amount.
            """
            self.progress(min(self.stat_progress+amount, self.stat_max))

        ## Wrappers for various achievement functionality
        def clear(self):
            """Clear this achievement from memory."""
            return achievement.clear(self.id)

        def get_progress(self):
            """Return this achievement's progress."""
            return achievement.get_progress(self.id)

        def grant(self):
            """
            Grant the player this achievement, and show a popup if this is
            the first time they've gotten it.
            """
            has_achievement = self.has()
            x = achievement.grant(self.id)
            if not has_achievement:
                # First time this was granted
                self.achievement_popup()
                # Save the timestamp
                self._timestamp = time.time()
                # Callback
                if myconfig.ACHIEVEMENT_CALLBACK is not None:
                    renpy.run(myconfig.ACHIEVEMENT_CALLBACK, self)
            # Double check achievement sync
            achievement.sync()
            return x

        def has(self):
            """Return True if the player has achieved this achievement."""
            return achievement.has(self.id)

        def progress(self, complete):
            """
            A plugin to the original Achievement class. Sets the current
            achievement progress to "complete".
            """
            has_achievement = self.has()
            x = achievement.progress(self.id, complete)
            if not has_achievement and self.has():
                # First time this was granted
                self.achievement_popup()
            return x

        def achievement_popup(self):
            """
            A function which shows an achievement screen to the user
            to indicate they were granted an achievement.
            """

            if renpy.is_init_phase():
                ## This is init time; we don't show a popup screen
                return
            elif not self.has():
                # Don't have this achievement, so it doesn't get a popup.
                return
            elif not myconfig.SHOW_ACHIEVEMENT_POPUPS:
                # Popups are disabled
                return

            if achievement.steamapi and not myconfig.INGAME_POPUP_WITH_STEAM:
                # Steam is detected and popups shouldn't appear in-game.
                return

            # Otherwise, show the achievement screen
            for i in range(10):
                if store.onscreen_achievements.get(i, None) is None:
                    store.onscreen_achievements[i] = True
                    break
            # Generate a random tag for this screen
            tag = get_random_screen_tag(6)
            renpy.show_screen('achievement_popup', a=self, tag=tag, num=i,
                _tag=tag)

        def AddProgress(self, amount=1):
            """Add amount of progress to this achievement."""
            return Function(self.add_progress, amount=amount)

        def Progress(self, amount):
            """Set this achievement's progress to amount."""
            return Function(self.progress, amount)

        def Toggle(self):
            """
            A developer action to easily toggle the achieved status
            of a particular achievement.
            """
            return [SelectedIf(self.has()),
                If(self.has(),
                    Function(self.clear),
                    Function(self.grant))]

        def Grant(self):
            """
            An action to easily achieve a particular achievement.
            """
            return Function(self.grant)

        @classmethod
        def reset(self):
            """
            A class method which resets all achievements and clears all their
            progress.
            """
            for achievement in self.all_achievements:
                achievement.clear()

        @classmethod
        def Reset(self):
            """
            A class method which resets all achievements and clears all their
            progress. This is a button action rather than a function.
            """
            return Function(self.reset)

        @classmethod
        def num_earned(self):
            """
            A class property which returns the number of unlocked achievements.
            """
            return len([a for a in self.all_achievements if a.has()])

        @classmethod
        def num_total(self):
            """
            A class property which returns the total number of achievements.
            """
            return len(self.all_achievements)


    class LinkedAchievement():
        """
        A class which can be used as part of an achievement callback to
        trigger an achievement when some subset of achievements is unlocked.

        Attributes:
        -----------
        links : dict
            A dictionary of the form {achievement.id : [list of final
            achievement ids]}. This is a reverse of the dictionary passed in
            to the constructor and is used to look up what final achievements
            are tied to a given achievement.
        final_to_list : dict
            A dictionary of the form {final_achievement.id : [list of
            achievement ids to check]}. This is the same as the dictionary
            passed in to the constructor, and is used to look up what
            achievements are needed to unlock a given final achievement.
        unlock_after_all : string
            If this is set to an achievement ID, then that achievement is
            unlocked after all other achievements are unlocked.
        """
        def __init__(self, **links):
            """
            Create a LinkedAchievement to be used as a callback.

            Parameters:
            ----------
            links : dict
                A dictionary of the form {final_achievement.id : [list of
                achievement ids to check]}. When all of the achievements in the
                list are unlocked, the final achievement is unlocked.
            """
            ## links comes in the form of
            ## {final_achievement.id : [list of achievement ids to check]}
            self.links = dict()

            values = links.values()
            if len(values) == 1 and 'all' in values:
                ## Special case for an achievement that's achieved after
                ## getting all achievements
                self.unlock_after_all = ''.join(links.keys())
                self.final_to_list = links
                return
            else:
                self.unlock_after_all = False

            ## Reverse-engineer a dictionary which corresponds to the things
            ## that are checked, and what they tie back to.
            for final_achievement, check_achievements in links.items():
                for check_achievement in check_achievements:
                    if check_achievement == final_achievement:
                        continue
                    if check_achievement not in links:
                        self.links[check_achievement] = [final_achievement]
                    else:
                        self.links[check_achievement].append(final_achievement)

            self.final_to_list = links

        def __call__(self, the_achievement):
            """
            A method which is called when an achievement is unlocked.
            It checks if the achievement is part of a list of achievements
            which are needed to unlock a given final achievement, and if the
            conditions needed to unlock that final achievement are met.
            If so, it grants that achievement.

            Parameters:
            -----------
            the_achievement : Achievement
                The achievement which was just granted.
            """
            if self.unlock_after_all:
                ## This unlocks after all achievements are earned
                if all([a.has() for a in Achievement.all_achievements
                        if a.id != self.unlock_after_all]):
                    fa = Achievement.achievement_dict.get(self.unlock_after_all)
                    if fa is not None:
                        fa.grant()
                return

            ## Find which final achievements this is attached to
            final_achievements = self.links.get(the_achievement.id, None)
            if not final_achievements:
                return

            ## Otherwise, see if this was the last achievement which was needed
            ## to unlock a given final_achievement.
            for final_achievement in final_achievements:
                lst = self.final_to_list.get(final_achievement, None)
                if lst is None:
                    continue
                ## Check if all the achievements in the list are unlocked
                if all([achievement.has(a) for a in lst]):
                    fa = Achievement.achievement_dict.get(final_achievement)
                    if fa is not None:
                        fa.grant()
            return

## Note: DO NOT change these configuration values in this block! See
## `achievements.rpy` for how to change them. This is just for setup so they
## exist in the game, and then you can modify them with `define` in a different
## file.
init -999 python in myconfig:
    _constant = True
    ## This is a configuration value which determines whether the in-game
    ## achievement popup should appear when Steam is detected. Since Steam
    ## already has its own built-in popup, you may want to set this to False
    ## if you don't want to show the in-game popup alongside it.
    ## The in-game popup will still work on non-Steam builds, such as builds
    ## released DRM-free on itch.io.
    INGAME_POPUP_WITH_STEAM = True
    ## The length of time the in-game popup spends hiding itself (see
    ## transform achievement_popout in achievements.rpy).
    ACHIEVEMENT_HIDE_TIME = 1.0
    ## True if the game should show in-game achievement popups when an
    ## achievement is earned. You can set this to False if you just want an
    ## achievement gallery screen and don't want any popups.
    SHOW_ACHIEVEMENT_POPUPS = True
    ## A callback, or list of callbacks, which are called when an achievement
    ## is granted. It is called with one argument, the achievement which
    ## was granted. It is only called if the achievement has not previously
    ## been earned.
    ACHIEVEMENT_CALLBACK = None

## Track the time each achievement was earned at
default persistent.achievement_timestamp = dict()
## Tracks the number of onscreen achievements, for offsetting when
## multiple achievements are earned at once
default onscreen_achievements = dict()
## Required for older Ren'Py versions so the vpgrid doesn't complain about
## uneven numbers of achievements, but True by default in later Ren'Py versions.
define config.allow_underfull_grids = True

# This, coupled with the timer on the popup screen, ensures that the achievement
# is properly hidden before another achievement can be shown in that "slot".
# If this was done as part of the timer in the previous screen, then it would
# consider that slot empty during the 1 second the achievement is hiding itself.
# That's why this timer is 1 second long.
screen finish_animating_achievement(num):
    timer myconfig.ACHIEVEMENT_HIDE_TIME:
        action [SetDict(onscreen_achievements, num, None), Hide()]

