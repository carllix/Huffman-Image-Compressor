import sys
from pathlib import Path
from typing import Dict, Tuple
import time
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich.prompt import Prompt
from rich.table import Table
from image_compressor import ImageCompressor


class CompressorCLI:
    def __init__(self):
        self.console = Console()
        self.input_dir = Path("test/input")
        self.output_dir = Path("test/output")
        self.setup_directories()

    def setup_directories(self):
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def show_welcome(self):
        welcome_msg = """
[bold cyan]Image Compressor Program[/bold cyan]
[yellow]A Huffman-based image compression tool[/yellow]
※ Only supports image files (PNG, JPG, JPEG)
        """
        self.console.print(Panel(welcome_msg, border_style="blue"))

    def is_valid_image(self, file_path: Path) -> Tuple[bool, str, tuple]:
        try:
            if file_path.suffix.lower() not in [".png", ".jpg", ".jpeg"]:
                return False, "Not an image file", (0, 0)
            with Image.open(file_path) as img:
                return True, "", img.size
        except Exception:
            return False, "Invalid or corrupted image file", (0, 0)

    def format_kb_size(self, size_bytes: int) -> str:
        size_kb = size_bytes / 1024
        return f"{size_kb:,.2f}".replace(",", ".") + " KB"

    def format_bits(self, bits: int) -> str:
        return f"{bits:,}".replace(",", ".") + " bits"

    def list_input_files(self) -> Dict[int, Path]:
        files = list(self.input_dir.glob("*"))
        if not files:
            self.console.print("[red]No files found in input directory![/red]")
            self.console.print(f"\nPlease add files to: [cyan]{self.input_dir}[/cyan]")
            sys.exit(1)

        table = Table(title="Available Files")
        table.add_column("Choice", style="cyan")
        table.add_column("Filename", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Dimensions", style="magenta")
        table.add_column("File Size", style="blue")

        file_map = {}
        choice_num = 1

        for file in files:
            is_valid, error_msg, dimensions = self.is_valid_image(file)
            file_size = self.format_kb_size(file.stat().st_size)

            if is_valid:
                file_map[choice_num] = file
                table.add_row(
                    str(choice_num),
                    file.name,
                    "[green]Image[/green]",
                    f"{dimensions[0]}x{dimensions[1]}",
                    file_size,
                )
                choice_num += 1
            else:
                table.add_row(
                    "[red]✗[/red]",
                    f"[red]{file.name}[/red]",
                    f"[red]{error_msg}[/red]",
                    "[red]N/A[/red]",
                    f"[red]{file_size}[/red]",
                )

        self.console.print(table)
        return file_map

    def compress_image(self, input_file: Path):
        compressor = ImageCompressor()
        output_base = self.output_dir / input_file.stem

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Compressing...", total=100)

            for i in range(50):
                time.sleep(0.02)
                progress.update(task, advance=1)

            stats = compressor.compress(str(input_file), str(output_base))

            progress.update(task, completed=100)

        return stats, output_base

    def decompress_image(self, input_base: Path, original_size: tuple):
        compressor = ImageCompressor()
        output_path = self.output_dir / f"{input_base.stem}_decompressed.png"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Decompressing...", total=100)

            for i in range(50):
                time.sleep(0.02)
                progress.update(task, advance=1)

            compressor.decode_image(
                f"{input_base}.bin",
                f"{input_base}_codes.json",
                str(output_path),
                original_size,
            )

            progress.update(task, completed=100)

        return output_path

    def show_results(
        self,
        stats: dict,
        input_file: Path,
        output_base: Path,
        decompressed_path: Path = None,
    ):
        results_table = Table(title="Compression Results")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green")

        results_table.add_row("Input File", str(input_file))
        results_table.add_row(
            "Image Size",
            f"{stats['original_size'][0]}x{stats['original_size'][1]} pixels",
        )
        results_table.add_row(
            "File Size", self.format_kb_size(input_file.stat().st_size)
        )
        results_table.add_row("Original Size", self.format_bits(stats["original_bits"]))
        results_table.add_row("\nOutput Files:", "")

        # Get compressed file sizes
        bin_file = Path(f"{output_base}.bin")
        codes_file = Path(f"{output_base}_codes.json")
        results_table.add_row(
            "  • Binary Data",
            f"{bin_file.name} ({self.format_kb_size(bin_file.stat().st_size)})",
        )
        results_table.add_row(
            "  • Huffman Codes",
            f"{codes_file.name} ({self.format_kb_size(codes_file.stat().st_size)})",
        )
        results_table.add_row(
            "Compressed Size", self.format_bits(stats["compressed_bits"])
        )
        results_table.add_row("Compression Ratio", f"{stats['compression_ratio']:.2f}%")

        if decompressed_path:
            _, _, dimensions = self.is_valid_image(decompressed_path)
            results_table.add_row("\nDecompressed File:", "")
            results_table.add_row(
                "  • Image File",
                f"{decompressed_path.name} ({self.format_kb_size(decompressed_path.stat().st_size)})",
            )
            results_table.add_row(
                "  • Image Size", f"{dimensions[0]}x{dimensions[1]} pixels"
            )

        self.console.print("\n")
        self.console.print(results_table)

    def run(self):
        self.show_welcome()

        while True:
            self.console.print("\n[yellow]Available files in input directory:[/yellow]")
            file_map = self.list_input_files()

            if not file_map:
                self.console.print(
                    "\n[red]No valid image files found! Please add some images to process.[/red]"
                )
                break

            choice = Prompt.ask(
                "\nSelect an image to compress (1-%d) or 'q' to quit" % len(file_map),
                choices=[str(i) for i in range(1, len(file_map) + 1)] + ["q"],
            )

            if choice.lower() == "q":
                self.console.print(
                    "\n[green]Thank you for using Image Compressor Program![/green]"
                )
                break

            input_file = file_map[int(choice)]
            self.console.print(f"\n[cyan]Processing:[/cyan] {input_file.name}")

            try:
                stats, output_base = self.compress_image(input_file)

                decompress = Prompt.ask(
                    "\nDo you want to decompress the image?",
                    choices=["y", "n"],
                    default="n",
                )

                decompressed_path = None
                if decompress.lower() == "y":
                    decompressed_path = self.decompress_image(
                        output_base, stats["original_size"]
                    )

                self.show_results(stats, input_file, output_base, decompressed_path)

            except Exception as e:
                self.console.print(f"\n[red]Error:[/red] {str(e)}")

            self.console.print("\n[yellow]Press Enter to continue...[/yellow]")
            input()
            self.console.clear()


if __name__ == "__main__":
    cli = CompressorCLI()
    cli.run()
