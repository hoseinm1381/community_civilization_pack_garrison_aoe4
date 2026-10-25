"""Prepare narrowly patched current official UI files; no installation/package."""
import hashlib, json, sys
from pathlib import Path
from xml.etree import ElementTree as ET
from common import ROOT, OUT, guard, write, sha
sys.path.insert(0, str(ROOT/'tools/release_072/vendor'))
from read_official_members import members, BASE

UI = ROOT/'assets/ui'
EVIDENCE = OUT/'hud/official'
PATHS = {'playerscores.xaml':'hud/controls/playerscores.xaml',
         'cardinalhudpage.xaml':'hud/pages/cardinalhudpage.xaml',
         'hudresources.xaml':'resources/hudresources.xaml'}

BUFFALO = '''
    <!-- Vietnam 0.7.10: local presentation, original China template untouched. -->
    <DataTemplate x:Key="VietnamBuffaloCounter" DataType="{x:Type model:HUDModelBase}">
        <Grid Width="{StaticResource SmallWidgetDisplayGridWidth}">
            <Canvas><Image Canvas.Right="-6" Canvas.Bottom="-2"
                Width="{StaticResource SmallWidgetDisplayBackgroundWidth}" Stretch="UniformToFill"
                Style="{DynamicResource HUDCivSpecific2BackgroundImage}" /></Canvas>
            <Button Height="{StaticResource HUDResourceButtonHeight}" Margin="6,0,8,10"
                HorizontalContentAlignment="Stretch" Style="{DynamicResource HUDButtonStyle}"
                Command="{Binding LocalPlayer.ScarModel[vietnam_buffalo_cycle]}"
                ToolTip="Water Buffalo — living / current limit. Click to select the next buffalo.">
                <Button.IsEnabled>
                    <MultiBinding Converter="{StaticResource MultiLogicalAnd}">
                        <Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_count]" Converter="{StaticResource GreaterCompare}" ConverterParameter="0" />
                        <Binding Path="IsReplay" Converter="{StaticResource InvBool}" />
                        <Binding Path="Replay.IsObserver" Converter="{StaticResource InvBool}" />
                    </MultiBinding>
                </Button.IsEnabled>
                <Grid><Grid.ColumnDefinitions><ColumnDefinition Width="Auto" /><ColumnDefinition Width="*" /></Grid.ColumnDefinitions>
                    <Image Width="27" Height="27" Margin="4,0,2,0" Source="/WPFGUI;component/images/vietnam_0710/buffalo.png" />
                    <TextBlock Grid.Column="1" HorizontalAlignment="Center" VerticalAlignment="Center" Style="{StaticResource nHUDBaseHeavyTextBlockStyle}">
                        <TextBlock.Text><MultiBinding Converter="{StaticResource LocalizedStringMultiConverter}" ConverterParameter="$11170906">
                            <Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_count]" />
                            <Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_cap]" />
                        </MultiBinding></TextBlock.Text>
                    </TextBlock>
                </Grid>
            </Button>
        </Grid>
    </DataTemplate>
    <DataTemplate x:Key="VietnamBuffaloSupervisionTemplate">
        <Border Width="20" Height="20" Background="#D020281B" BorderBrush="#E7C66F" BorderThickness="1" CornerRadius="10" IsHitTestVisible="False">
            <Image Width="16" Height="16" Source="/WPFGUI;component/images/vietnam_0710/buffalo.png" IsHitTestVisible="False" />
        </Border>
    </DataTemplate>
'''

def main():
    guard()
    assert (OUT/'baseline/source.zip').is_file(), 'Freeze required'
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    found = {}
    for name, data in members('UI.sga', lambda n: n in PATHS):
        # UI.sga also contains a caster-mode PlayerScores with the same basename.
        text = data.decode('utf-8-sig')
        if name == 'playerscores.xaml' and 'ImageSource="{Binding RaceIcon,' not in text:
            continue
        assert name not in found, name
        found[name] = data
    assert set(found) == set(PATHS)
    for name, original in found.items():
        evidence = EVIDENCE/name
        if evidence.exists(): assert evidence.read_bytes() == original, 'Official UI changed; review required'
        else: evidence.write_bytes(original)
        text = original.decode('utf-8-sig').replace('\r\n', '\n')
        if name == 'playerscores.xaml':
            anchor = '''                                </Grid.Background>
                            </Grid>'''
            assert text.count(anchor) == 1
            text = text.replace(anchor, '''                                </Grid.Background>
                                <Image Source="/WPFGUI;component/images/vietnam_0710/dai_viet_dragon.png" Stretch="Fill"
                                    Visibility="{Binding ScarModel[vietnam_hud], Converter={StaticResource BoolToVis}, FallbackValue=Collapsed}" />
                            </Grid>''')
        elif name == 'cardinalhudpage.xaml':
            anchor = '                                                ContentTemplate="{StaticResource ChineseImperialOfficers}"\n'
            assert text.count(anchor) == 1
            text = text.replace(anchor, '')
            marker = '                                <!--  Chinese Imperial Officers  -->'
            start = text.index(marker)
            pos = text.index('                                    <ContentControl.Visibility>', start)
            text = text[:pos] + '''                                    <ContentControl.Style>
                                        <Style TargetType="ContentControl">
                                            <Setter Property="ContentTemplate" Value="{StaticResource ChineseImperialOfficers}" />
                                            <Style.Triggers>
                                                <DataTrigger Binding="{Binding LocalPlayer.ScarModel[vietnam_hud]}" Value="True">
                                                    <Setter Property="ContentTemplate" Value="{StaticResource VietnamBuffaloCounter}" />
                                                </DataTrigger>
                                            </Style.Triggers>
                                        </Style>
                                    </ContentControl.Style>
''' + text[pos:]
        else:
            assert text.count('</ResourceDictionary>') == 1
            text = text.replace('</ResourceDictionary>', BUFFALO+'\n</ResourceDictionary>')
        ET.fromstring(text)
        dest = UI/PATHS[name]
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(text,encoding='utf-8',newline='\n')
    print('Prepared 3 official-derived XML overrides. Run hud_receipt.py after raster export and tests.')

if __name__ == '__main__': main()

