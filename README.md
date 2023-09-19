# Achievements for Ren'Py

Included in these files is a system which wraps the existing achievement code found in Ren'Py to make it easy to declare achievements which you can grant to the player during gameplay.

## Initial Setup

To start, place `achievement_backend.rpy` and `achievements.rpy` into your project's `game/` folder. The code you are concerned with is found in `achievements.rpy` and includes several examples to get started.

## The Achievement Class

Achievements should all be set up using the built-in Achievement class, which has several properties and methods you can take advantage of.

## Properties

Achievements are declared like the following:

```renpy
define sample_achievement = Achievement(
    name=_("A sample achievement"),
    id="sample_achievement",
    description=_("A sample description"),
    unlocked_image="gui/achievements/sample_achievement.png",
    hidden=True,
)
```

The Achievement class takes the following parameters:

`name`
    A string. Required. The human-readable name of the achievement, to be used in popups and in the achievement gallery.

`id`
    A string. The ID of the achievement. Must be unique. This is the ID you should use to register this achievement in Steamworks so they can sync.

`description`
    A string. The description for this achievement as it should appear in the achievement gallery and/or popups.

`unlocked_image`
    A displayable (usually an image path like "achievements/endings.png") which will be used in the gallery and on the achievement popup when this achievement is unlocked.

`locked_image`
    A displayable (usually an image path) which will be used in the gallery when this achievement is locked. If not provided, it defaults to the "locked_achievement" image, which can be found declared in `achievements.rpy`. You can re-declare this to point to whichever image you like.

`stat_max`
    An integer. If provided, this is used to track progress towards completion of an achievement. Reaching this number means the achievement is completed. So, for example, if you have an achievement for reading all 10 chapters in your game, then `stat_max` would be `10` and you'd use the `progress` or `add_progress` methods (described below) to add progress as the player progresses through the chapters.

`stat_modulo`
    An integer. This is a bit confusing but perhaps this use case will make it clearer: say you have an achievement which has 300 steps to complete (maybe it's collecting items or it's tracking completion to 100% complete the game). In order to avoid sending progress updates to Steam of 0.3% completion towards the goal, we only want to send an update every time the player gets 1% closer to the goal. In such a case, you'd set `stat_modulo` to `3`, because `300 % 3 = 0` (300 modulo 3 equals 0). When this happens, Ren'Py sends a progress update to Steam.
    If this sounds confusing, I recommend the next property instead.

`stat_update_percent`
    A slightly simpler way to understand `stat_modulo`. If, in the previous example where there were 300 things to track on the way to finishing the achievement, you wanted to send an update to Steam every 1%, you would set `stat_update_percent=1`. If you wanted to send it every 5% completion it would instead be `stat_update_percent=5`. Meeting or exceeding the `stat_max` will always grant the achievement regardless of what `stat_modulo` or `stat_update_percent` are, so it doesn't have to be perfectly divisible.

`hidden`
    If True, both the achievement name and its description are replaced by "???" in the achievement gallery screen. Useful for achievements for which the name and description would be a spoiler.

`hide_description`
    If True, the description will be hidden. This can be used in combination with `hidden` to hide just the name and not the description, or just the description and not the name.
    `hidden=True, hide_description=False` -> The name is ???, the description is not hidden.
    `hidden=False, hide_description=True` -> The name is not hidden, the description is ???
    `hidden=True` -> the name and description are ???
    You can also set `hide_description` to a string, in which case that string will be shown as the description before the achievement has been granted e.g. `hide_description=_("A certain someone wants to see you...")`

### Regular Methods

`get_timestamp`
    This method takes one argument, `format`. It should correspond to a [strftime](https://strftime.org/) format, which will be used for the returned timestamp. See `achievements.rpy` for an additional example of how to use this to adjust how the timestamp displays.

`add_progress`
    This method takes one argument, `amount`, which is the amount to add to the progress of the achievement. An achievement must be using `stat_max` for this method to make sense. If the achievement had 3/5 progress, then `sample_achievement.add_progress(1)` would result in it having 4/5 progress.

`progress`
    This method takes one argument, `complete`, which is the number the progress for this achievement will be *set* to. Unlike `add_progress`, it does not add progress, merely sets it to the provided number. So, if an achievement had 2/5 progress, then `sample_achievement.progress(3)` would set it to 3/5 progress, since progress was set to 3.
    This can be most useful if you're using something like, say, a persistent set to keep track of endings. You can plug the length of the set into the `progress` method to prevent double-counting progress points e.g. `endings_achievement.progress(len(persistent.all_endings))`.

`clear`
    This method will clear this achievement from the list of unlocked achievements. Best used for testing. It takes no arguments. e.g. `sample_achievement.clear()`

`get_progress`
    This method will return the current progress for the achievement e.g. `sample_achievement.get_progress()`.

`grant`
    This method will grant the achievement to the player e.g. `sample_achievement.grant()`. If a player has already earned this achievement, it does nothing.

`has`
    This method returns True if this achievement has been granted to the player, and False if not e.g. `sample_achievement.has()`

`num_earned`
    This is a class method which can be invoked using the Achievement class name instead of a specific Achievement variable. It returns the number of earned achievements in total e.g. `Achievement.num_earned()`.

`num_total`
    This is a class method which can be invoked using the Achievement class name instead of a specific Achievement variable. It returns the total number of achievements declared in the game e.g. `Achievement.num_total()`.
    You can see both this and `Achievement.num_earned()` used in the header of the `achievement_gallery` screen in `achievements.rpy`.

`reset`
    This is a class method which can be invoked using the Achievement class name instead of a specific Achievement variable. It resets the progress of all achievements in the game e.g. `Achievement.reset()`

### Button Actions

`AddProgress`
    This is the screen language equivalent of the `add_progress` method. It will add the provided progress to the existing progress already on the achievement e.g. `action sample_achievement.AddProgress(1)` will add 1 point of progress towards `sample_achievement`. Note that this should probably be wrapped in some kind of condition to prevent adding progress over and over.

`Progress`
    This is the screen language equivalent of the `progress` method. It takes one argument, the amount to set the progress to. `action sample_achievement.Progress(3)` will set sample_achievement's progress to 3 regardless of its previous value.

`Grant`
    This is the screen language equivalent of the `grant` method. It does not take any arguments e.g. `action sample_achievement.Grant()`

`Toggle`
    This is a special method intended to be used for testing. If an achievement has been granted, clicking a button with this Toggle method will clear it from the unlocked achievements. If it has not been granted, clicking the button will grant it. e.g. `sample_achievement.Toggle()`

`Reset`
    This is a special method which can be used to reset the progress of all achievements at once. It is a class method, and is thus always called like `action Achievement.Reset()`.

## Configuration Values

Besides the Achievement class, there are a few configuration values you can set up to further customize the behaviour of achievements. You can find these at the top of `achievements.rpy`.

`myconfig.INGAME_POPUP_WITH_STEAM`
    If True, the default, the in-game popup will appear even when Steam integration is detected. Since Steam has its own built-in popup, you may want to set this to False if you don't want two popups on the screen. If this is False, the in-game popup will still work on non-Steam builds, such as builds released DRM-free on itch.io.

`myconfig.ACHIEVEMENT_HIDE_TIME`
    This should be set to the length, in seconds, that the in-game popup spends hiding itself. See `transform achievement_popup` for where this is used.

`myconfig.SHOW_ACHIEVEMENT_POPUPS`
    If True, the default, an in-game popup screen is displayed when getting an achievement. You may also set this to False to disable the in-game popup altogether for all builds if you just want the other Achievement features.

`myconfig.ACHIEVEMENT_CALLBACK`
    A callback, or a list of callbacks, which are called when an achievement is granted. The callback is called with one argument, the achievement which was granted. It is only called if the achievement has not previously been earned.
    You can use this alongside the included `LinkedAchievement` class to set up achievements which automatically unlock when other achievements are unlocked. This is explained in further detail below.

`achievement.steam_position`
    This is a configuration value provided by Ren'Py itself. It will set the position of the Steam popup and can be set to one of: `"top_left"`, `"top_right"`, `"bottom_left"`, or `"bottom_right"`. If you are using the built-in achievement popups of this system alongside Steam's, you may want to set this to ensure the popups do not appear in the same location.

## LinkedAchievement

LinkedAchievement is a special class designed to be used alongside `myconfig.ACHIEVEMENT_CALLBACK` which provides an easy way of adding a callback that will automatically unlock a specific achievement when some other subset of achievements have been unlocked.

### Platinum Achievements

There are two main ways you might use `LinkedAchievement` as part of `myconfig.ACHIEVEMENT_CALLBACK` - first is for a "platinum" achievement, which unlocks when all other achievements have been granted. This special case can be handled via:

```renpy
define myconfig.ACHIEVEMENT_CALLBACK = LinkedAchievement(platinum_achievement="all")
```

In this case, `platinum_achievement` must be the ID field of the "platinum" achievement (which must be declared as an Achievement).

### Connected Achievements

The second way you may want to use LinkedAchievement is to trigger an achievement when some subset of other Achievements have been granted. Using the LinkedAchievement class, this looks like:

```renpy
define myconfig.ACHIEVEMENT_CALLBACK = [
    LinkedAchievement(all_endings_achievement=["good_end", "bad_end", "normal_end"]),
]
```

In this example, `all_endings_achievement` is the ID of the achievement which will be unlocked when the other provided achievements are granted, and `"good_end"`, `"bad_end"`, and `"normal_end"` are the IDs of the achievements which, when all granted, will trigger the provided achievement.

## Final Notes

You can check out my website, https://feniksdev.com for more Ren'Py tutorials, and subscribe to feniksdev.itch.io so you don't miss out on future Ren'Py tool releases!
