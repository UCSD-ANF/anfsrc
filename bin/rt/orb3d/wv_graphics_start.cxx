#include <wv_graphics_start.h>

void *
graphics_start(void *dlp) {

	Wv_datalink *dl = (Wv_datalink *) dlp;

        cout<<"Inside graphics_start"<<endl;
        //CWindow *w = (CWindow *) win;
        //CWindow *w ;

        SoDB::init();
        SoInteraction::init(); // TODO : Do I need SOInteraction?

        int a;
        char** av;
        //glutInit(&a,av);
        //glutInit();
        cout<<"Done glutInit()"<<endl;

        int width = 1280;
        int height = 1024;
        int xloc = 0;
        int yloc = 0;
        CWindow *w = new CWindow( "ORB3D : Real Time Display for the ANZA network", width, height, xloc, yloc, dl );
        w->eventKeyUp( 'p',     w->play);
        w->eventKeyUp( 'y',     w->spinOnY);
        w->eventKeyUp( 't',     w->toggleText);
        w->eventKeyUp( ',',     w->previous);
        w->eventKeyUp( '.',     w->next);
        w->eventKeyUp( 13,      w->spin);
        w->eventKey( ESCAPE,w->Quit );
        w->eventKey( 'f',       w->fullScreen);
        w->eventKey( 'u',       w->zoomIn);
        w->eventKey( 'o',       w->zoomOut);
        w->eventKey( 'q',       w->RotateZ);
        w->eventKey( 'e',       w->CounterRotateZ);
        w->eventKey( 'a',       w->RotateY);
        w->eventKey( 'd',       w->CounterRotateY);
        w->eventKey( 's',       w->RotateX);
        w->eventKey( 'w',       w->CounterRotateX);
        w->eventKey( 'i',       w->PanUp);
        w->eventKey( 'k',       w->PanDown);
        w->eventKey( 'j',       w->PanLeft);
        w->eventKey( 'l',       w->PanRight);
        w->eventKey( '=',       w->PlaybackFaster);
        w->eventKey( '+',       w->PlaybackFaster);
        w->eventKey( '_',       w->PlaybackSlower);
        w->eventKey( '-',       w->PlaybackSlower);
        w->eventKey( '[',       w->SpinSlower);
        w->eventKey( ']',       w->SpinFaster);
        w->eventKey( '{',       w->SpinSlower);
        w->eventKey( '}',       w->SpinFaster);
        w->eventKey( 'r',   w->reset);
        w->mainLoop(dlp);

}
