from rich import print


def pinfo(*obj, end='\n'):
    text = ' '.join(map(str, obj)).strip()
    format_text = f'[#ffffff]INFO:[/#ffffff] [green]{text}[/green]'
    print(format_text, end=end)


def perror(*obj, end='\n'):
    text = ' '.join(map(str, obj)).strip()
    format_text = f'[#ffffff]ERROR:[/#ffffff] [red]{text}[/red]'
    print(format_text, end=end)


# Example usage:
pinfo("This is an info message.")
perror("This is an error message.")