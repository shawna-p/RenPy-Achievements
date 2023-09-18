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
                return _("???{#hidden_achievement_description}")
            else:
                return self._description

        def AddProgress(self, amount=1):
            """Add amount of progress to this achievement."""
            return Function(self.add_progress, amount=amount)

        def Progress(self, amount):
            """Set this achievement's progress to amount."""
            return Function(self.progress, amount)

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


## Track the time each achievement was earned at
default persistent.achievement_timestamp = dict()
## Tracks the number of onscreen achievements, for offsetting when
## multiple achievements are earned at once
default onscreen_achievements = dict()

define config.allow_underfull_grids = True

# This, coupled with the timer on the popup screen, ensures that the achievement
# is properly hidden before another achievement can be shown in that "slot".
# If this was done as part of the timer in the previous screen, then it would
# consider that slot empty during the 1 second the achievement is hiding itself.
# That's why this timer is 1 second long.
screen finish_animating_achievement(num):
    timer myconfig.ACHIEVEMENT_HIDE_TIME:
        action [SetDict(onscreen_achievements, num, None), Hide()]

