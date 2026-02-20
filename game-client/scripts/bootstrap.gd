extends Node2D

const BOOTSTRAP_ARG_PREFIX := "--bootstrap="

func _ready() -> void:
    var bootstrap_path := _find_bootstrap_arg(OS.get_cmdline_user_args())
    if bootstrap_path.is_empty():
        print("GOK game-client bootstrap: no launcher bootstrap path provided")
        return

    var file := FileAccess.open(bootstrap_path, FileAccess.READ)
    if file == null:
        push_error("GOK game-client bootstrap: failed to open bootstrap file: " + bootstrap_path)
        return

    var payload := file.get_as_text()
    file.close()
    print("GOK game-client bootstrap loaded from: " + bootstrap_path)
    print(payload)

func _find_bootstrap_arg(args: PackedStringArray) -> String:
    for raw_arg in args:
        if raw_arg.begins_with(BOOTSTRAP_ARG_PREFIX):
            return raw_arg.substr(BOOTSTRAP_ARG_PREFIX.length())
    return ""
