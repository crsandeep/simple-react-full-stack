import React from "react";
import { Responsive, WidthProvider } from 'react-grid-layout';
import "../css/react-grid-layout-styles.css";
import "../css/react-resizable-styles.css";
import "../css/SpaceGrid.css";
import PropTypes from 'prop-types';

import {Row, Col, ButtonToolbar, Spinner, Alert} from 'react-bootstrap';
import {IconButton,} from '@material-ui/core/';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import EditIcon from '@material-ui/icons/Edit';
import SaveIcon from '@material-ui/icons/Save';
import DeleteIcon from '@material-ui/icons/Delete';
import HighlightOffIcon from '@material-ui/icons/HighlightOff';
import TouchAppIcon from '@material-ui/icons/TouchApp';
import VisibilityIcon from '@material-ui/icons/Visibility';

const ResponsiveReactGridLayout = WidthProvider(Responsive);

function SpaceGrid(props){
    const [readMode, setReadMode] = React.useState(false);

    const layoutBreakpoints = { lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 };
    const layoutColumns = { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 };

    return (
        <div>
            {
                //page loading mask
                props.formState.pageLoading === true &&
                <div className="overlay">
                    <Spinner animation="border" role="status" size="lg" style={{ width: 10 + 'rem', height: 10 + 'rem' }}
                    className='mt-5'>
                    <span className="sr-only">Loading...</span>
                    </Spinner>
                    <h5>Loading...</h5>
                </div>
            }
            <Row className="justify-content-md-center">
                <Col xs={9} md={9}>
                    <ButtonToolbar >
                        <IconButton aria-label="New" onClick={props.handleNew}>
                            <AddCircleOutlineIcon />
                        </IconButton>
                        <IconButton aria-label="Save" onClick={props.handleSave}>
                            <SaveIcon />
                        </IconButton>
                        <IconButton aria-label="Cancel" onClick={props.handleCancel}>
                            <HighlightOffIcon />
                        </IconButton>
                    </ButtonToolbar>
                </Col>
                <Col xs={3} md={3}>
                    {
                        // props.gridLayout.lg != null && props.gridLayout.lg.length>0 &&
                        props.gridLayout != null && props.gridLayout.length>0 &&
                            <div>
                                Current Mode:
                                <IconButton aria-label="Toggle Mode" onClick={()=>{setReadMode(!readMode); props.handleToggleMode(readMode)}}>
                                    {
                                        readMode ?
                                            <EditIcon />
                                        : <VisibilityIcon/>
                                    }
                                </IconButton>
                            </div>
                    }
                </Col>
                
            </Row>
            <Row>
                <Col xs={12} md={12}>
                    {
                        // props.gridLayout.lg != null && props.gridLayout.lg.length>0?
                        props.gridLayout != null && props.gridLayout.length>0?
                            <ResponsiveReactGridLayout 
                                layouts={props.gridLayout}
                                onLayoutChange={(currLayout, allLayouts) =>
                                    props.handleUpdateLayout(currLayout, allLayouts)
                                }
                                breakpoints={layoutBreakpoints}
                                cols={layoutColumns}
                            >
                                {
                                    // props.gridLayout.lg.map(grid => {
                                    props.gridLayout.map(grid => {
                                        return <div key={grid.i} className='spaceGrid-grid'>
                                            <div>
                                                <h1>{grid.i}</h1>
                                                <ButtonToolbar className='spaceGrid-btn'>
                                                    <IconButton aria-label="select" onClick={()=>props.handleSelect(grid.i)}>
                                                        <TouchAppIcon />
                                                    </IconButton>
                                                    <IconButton aria-label="delete" onClick={() => props.handleRemove(grid.i)}>
                                                        <DeleteIcon />
                                                    </IconButton>
                                                </ButtonToolbar>
                                            </div>
                                        </div>
                                    })
                                }
                            </ResponsiveReactGridLayout>
                        :<Alert variant='info'>Please add new grid to start manage your space!</Alert>
                    }
                </Col>
            </Row>
        </div>
    );
}

SpaceGrid.propTypes = {
    // gridLayout: PropTypes.array,
    // spaceId: PropTypes.number,
    // formState: PropTypes.object,
    handleNew:PropTypes.func.isRequired,
    handleToggleMode:PropTypes.func.isRequired,
    handleSave:PropTypes.func.isRequired,
    handleCancel:PropTypes.func.isRequired,
    handleUpdateLayout:PropTypes.func.isRequired,
    handleRemove:PropTypes.func.isRequired,
    handleSelect:PropTypes.func.isRequired
}

export default SpaceGrid;