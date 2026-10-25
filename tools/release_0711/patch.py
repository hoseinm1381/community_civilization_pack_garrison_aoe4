"""Exact reversible 0711 edits over frozen 0710 sources."""
import zipfile
from common import *

def transforms(name,text):
    if name=='assets/scar/vietnam/presentation.scar':
        text=text.replace('import("ui.scar")','import("ui.scar")\nimport("vietnam/presentation_data.scar")\nimport("vietnam/presentation_badges.scar")',1)
        text=text.replace('model.vietnam_buffalo_cap = 0','model.vietnam_buffalo_cap = 0\n        model.vietnam_buffalo_text = "0/0"')
        text=text.replace('model.vietnam_buffalo_cap = Player_GetCurrentPopulationCap(player.id, CT_Medic)',
            'model.vietnam_buffalo_cap = VietnamPresentationData.buffaloCap\n            model.vietnam_buffalo_text = string.format("%d/%d", model.vietnam_buffalo_count, model.vietnam_buffalo_cap)')
    elif name=='assets/scar/vietnam/paddy_wood.scar':
        needle='    if watch.marker ~= nil and (not visible or watch.markerPaddy ~= watch.paddy) then'
        text=text.replace(needle,'    if visible then\n        visible = Misc_IsPosOnScreen(Entity_GetPosition(paddy), 0.90)\n    end\n'+needle,1)
        text=text.replace('DataTemplate = "VietnamBuffaloSupervisionTemplate"}',
            'DataTemplate = "VietnamBuffaloSupervisionTemplate", VietnamQuietSupervision = true}',1)
    elif name=='assets/ui/resources/hudresources.xaml':
        start=text.index('    <DataTemplate x:Key="VietnamBuffaloCounter"')
        before,custom=text[:start],text[start:]
        old='''<TextBlock.Text><MultiBinding Converter="{StaticResource LocalizedStringMultiConverter}" ConverterParameter="$11170906">
                            <Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_count]" />
                            <Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_cap]" />
                        </MultiBinding></TextBlock.Text>'''
        assert old in custom
        custom=custom.replace(old,'<TextBlock.Text><Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_text]" /></TextBlock.Text>')
        custom=custom.replace('Width="20" Height="20" Background="#D020281B" BorderBrush="#E7C66F" BorderThickness="1" CornerRadius="10"',
            'Width="14" Height="14" Background="#9020281B" BorderBrush="#A8B79B6D" BorderThickness="1" CornerRadius="7" Opacity="0.65"')
        custom=custom.replace('<Image Width="16" Height="16"','<Image Width="10" Height="10"')
        text=before+custom
    elif name=='assets/ui/hud/pages/cardinalhudpage.xaml':
        start=text.index('<!--  Position tags  -->');end=text.index('<!--  Hint Points',start)
        before,region,after=text[:start],text[start:end],text[end:]
        assert region.count('esControls:TagAdorner.IsTagged="True"')==1
        region=region.replace('''                                <FrameworkElement esControls:TagAdorner.AlignmentMode="Relative"''','''                                <Grid>
                                <FrameworkElement esControls:TagAdorner.AlignmentMode="Relative"''',1)
        region=region.replace('                                                  esControls:TagAdorner.IsTagged="True"\n','',1)
        tail='esControls:TagAdorner.VerticalAnchor="Bottom" esControls:TagAdorner.VerticalPlacement="Top" />'
        replacement='''esControls:TagAdorner.VerticalAnchor="Bottom" esControls:TagAdorner.VerticalPlacement="Top">
                                    <FrameworkElement.Style>
                                        <Style TargetType="FrameworkElement">
                                            <Setter Property="esControls:TagAdorner.IsTagged" Value="True" />
                                            <Style.Triggers>
                                                <DataTrigger Binding="{Binding TagData.Data[VietnamQuietSupervision]}" Value="True">
                                                    <Setter Property="esControls:TagAdorner.IsTagged" Value="False" />
                                                </DataTrigger>
                                            </Style.Triggers>
                                        </Style>
                                    </FrameworkElement.Style>
                                </FrameworkElement>
                                <!-- Private work marker bypasses tutorial arrow, animation and clamping. -->
                                <ContentControl Content="{Binding TagData}" Margin="0,-18,0,0" IsHitTestVisible="False"
                                                ContentTemplate="{StaticResource VietnamBuffaloSupervisionTemplate}">
                                    <ContentControl.Style>
                                        <Style TargetType="ContentControl">
                                            <Setter Property="Visibility" Value="Collapsed" />
                                            <Style.Triggers>
                                                <DataTrigger Binding="{Binding TagData.Data[VietnamQuietSupervision]}" Value="True">
                                                    <Setter Property="Visibility" Value="Visible" />
                                                </DataTrigger>
                                            </Style.Triggers>
                                        </Style>
                                    </ContentControl.Style>
                                </ContentControl>
                                </Grid>'''
        assert region.count(tail)==1;region=region.replace(tail,replacement,1)
        text=before+region+after
    else:raise ValueError(name)
    return text

CHANGED=('assets/scar/vietnam/presentation.scar','assets/scar/vietnam/paddy_wood.scar',
    'assets/ui/resources/hudresources.xaml','assets/ui/hud/pages/cardinalhudpage.xaml')

def main():
    guard()
    with zipfile.ZipFile(OUT/'baseline/source.zip') as z:
        for name in CHANGED:
            old=z.read(name).decode('utf-8-sig').replace('\r\n','\n')
            p=ROOT/name;current=p.read_text(encoding='utf-8-sig')
            new=transforms(name,old)
            assert current in (old,new),('Unowned edit',name)
            p.write_text(new,encoding='utf-8',newline='\n')
    print('PATCHED',len(CHANGED),'presentation files')

if __name__=='__main__':main()
