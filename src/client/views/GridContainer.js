import React from "react";
import { withRouter } from "react-router";
import { connect } from 'react-redux'
import _ from "lodash";

import "../css/react-grid-layout-styles.css";
import "../css/react-resizable-styles.css";
import { GridComp } from '../components/'

import { layoutCreate } from '../actions/layoutAction'

import axios from 'axios';

class GridContainer extends React.Component {

    constructor(props) {
        super(props)
        this.state = {
            gridLayouts: {
                lg: [],
            },
            itemCount: 0,
            isEditMode: false,
            isSaved: false,
            userId: 1,
            wardobeId: 1
        }


        //bind handler
        this.generateItem = this.generateItem.bind(this)
        this.layoutChangeHandler = this.layoutChangeHandler.bind(this);
        this.backToLoginHandler = this.backToLoginHandler.bind(this)
        this.clearItemHandler = this.clearItemHandler.bind(this);
        this.toggleItemModeHandler = this.toggleItemModeHandler.bind(this);
        this.addNewItemHandler = this.addNewItemHandler.bind(this);
        this.removeHandler = this.removeHandler.bind(this)
        this.btnHandler = this.btnHandler.bind(this);
        this.saveLayoutHandler = this.saveLayoutHandler.bind(this);

        this.loadLayoutHandler = this.loadLayoutHandler.bind(this);

    }

    componentWillMount() {
        this.loadLayoutHandler()
    }

    //handler START

    clearItemHandler() {
        this.setState({
            gridLayouts: { lg: [] },
            itemCount: 0,
        });
    } 

    toggleItemModeHandler() {
        this.setState({
            isEditMode: !this.state.isEditMode
        });
        const currMode = this.state.isEditMode;
        let updatedList = this.state.gridLayouts.lg.map(obj => {
            return { ...obj, static: currMode }
        })

        this.setState({
            gridLayouts: { lg: updatedList }
        })
    }

    addNewItemHandler = (event) => {
        let nextId = this.state.itemCount + 1;
        this.setState({
            itemCount: nextId
            , gridLayouts: {
                lg: this.state.gridLayouts.lg.concat({
                    i: '' + nextId,
                    x: 0,
                    y: Infinity, // puts it at the bottom
                    w: 1,
                    h: 1
                })
            }
        })
        console.log("Add new item " + this.state.itemCount)
    };

    layoutChangeHandler(layout, layoutInJson) {
        this.setState({ gridLayouts: layoutInJson });
        // this.saveLayout(layoutInJson)
        console.log("onLayoutChange: "+ JSON.stringify(layoutInJson));
    }

    btnHandler = (event) => {
        event.stopPropagation();
        console.log('btnHandler, ' + event.target.id)
    };


    removeHandler = (event, itemKey) => {
        event.stopPropagation();
        this.setState({
            gridLayouts: { lg: _.reject(this.state.gridLayouts.lg, { i: itemKey }) },
            itemCount: this.state.itemCount - 1
        });
        console.log('removeHandler, ' + itemKey + ', ' + event.target.id)
    }
    
    backToLoginHandler() {
        console.log("Redirect - Login page")
        this.props.history.push('/login');

    }


    saveLayoutHandler = (event) => {
        // let uname = this.state.uname;
        const self = this;
        const dataMatrix = this.state.gridLayouts;
        const wardobeId = this.state.wardobeId;
        if(dataMatrix !=null){
            if(this.state.isSaved){
                axios.put(`http://localhost:3000/wardrobeLayout/${wardobeId}`, {
                    dataMatrix,
                    wardobeId
                }).then(function (response) {
                    self.setState({ isSaved: true});
                    this.props.onLayoutSave(response.data.dataMatrix);
                }).catch(function (error) {
                    console.log("ERROR: "+error);
                });
            }else{
                axios.post('http://localhost:3000/wardrobeLayout', {
                    dataMatrix,
                    wardobeId
                }).then(function (response) {
                    self.setState({ isSaved: true});
                    this.props.onLayoutSave(response.data.dataMatrix);
                }).catch(function (error) {
                    console.log("ERROR: "+error);
                });
            }
        }
    };

    loadLayoutHandler = (event) => {
        const self = this;

        axios.get(`http://localhost:3000/wardrobeLayout/${this.state.wardobeId}`)
        .then(function (response) {
            if(response.data.dataMatrix !=null && response.data.dataMatrix.lg.length>0){
                self.setState(
                    {
                        gridLayouts: response.data.dataMatrix
                        , itemCount: response.data.dataMatrix.lg.length
                        , isSaved: true
                    }
                )
            }
        }).catch(function (error) {
            console.log("ERROR: "+error);
        });
    };
    //handler END

    render() {
        return (
            <div>
                <GridComp
                    authFlag= {this.props.authFlag}
                    wardobeId={this.props.wardobeId}
                    drawerCount={this.props.drawerCount}
                    backToLoginHandler = {this.backToLoginHandler}
                    gridLayouts={this.state.gridLayouts}
                    generateItem={this.generateItem}
                    layoutChangeHandler={this.layoutChangeHandler}
                    clearItemHandler={this.clearItemHandler}
                    toggleItemModeHandler={this.toggleItemModeHandler}
                    addNewItemHandler={this.addNewItemHandler}
                    saveLayoutHandler={this.saveLayoutHandler}
                    loadLayoutHandler={this.loadLayoutHandler}
                />
            </div>
        )
    }


    generateItem(item) {
        
        let drawerStyle = {
            // backgroundColor: item.color
            // backgroundColor: '#ffffe6'
            backgroundColor: 'grey'
            //backgroundImage: `url(https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQhv7H2yhqSh1J6sGL8RZ-vccJ2vzHykE2Jff_TI27VMuNjmI2D&s)`
            , backgroundSize: '100% 100%'
            , backgroundRepeat: 'no-repeat'
        }

        const manageStyle = {
            position: "absolute",
            left: "35%",
            right: "35%",
            top: "100px",
            color: 'blue',
            textDecorationLine: 'underline',
            cursor: "pointer"
        };

        const removeStyle = {
            position: "absolute",
            right: "2px",
            top: 0,
            cursor: "pointer"
        };

        return (
            <div key={item.i} style={drawerStyle}>
                <div>
                    <h1>{item.i}</h1>
                    <span
                        style={removeStyle}
                        onMouseDown={(event) => this.removeHandler(event, item.i)}
                        onTouchStart={(event) => this.removeHandler(event, item.i)}
                    >
                        x
                    </span>
                    <span id={"btn_"+item.i}
                        style={manageStyle}
                        onMouseDown={this.btnHandler}
                        onTouchStart={this.btnHandler}
                    >
                        Manage
                    </span>
                </div>
            </div>
        );
    }
}

const mapStateToProps = (state) => {
    console.log('mapStateToProps, ' + state.authReducer.authFlag)
    return {
        authFlag: state.authReducer.authFlag,
        uname: state.authReducer.uname,
        wardobeId: state.wardobeReducer.wardobeId,
        drawerCount: state.wardobeReducer.drawerCount
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        onLayoutSave: (layout)=>{
            console.log("mapDispatchToProps, " + layout)
            dispatch(layoutCreate(layout))
        }
    }
}

export default withRouter(
    connect(
        mapStateToProps, mapDispatchToProps
    )(GridContainer)
)